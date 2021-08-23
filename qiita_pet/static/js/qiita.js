/*
 * bootstrapAlert will add a Bootstrap alert message to the body of the current
 * page.
 *
 * @param message: Message to display
 * @param severit: One of 'danger', 'info', 'warning' or 'success'.
 * @param timeout: OPTIONAL. When given, time (in ms) before alert fades out
 *
 */

var timeoutHandleForBoostrapAlert = null;

function bootstrapAlert(message, severity, timeout){
  // make timeout an optional parameter
  timeout = timeout || -1;

  severity = typeof severity !== 'undefined' ? severity : 'danger';
  $("#alert-message").remove();
  var alertDiv = $('<div>', { 'class': 'alert fade in alert-'+severity, 'role': 'alert', 'id': 'alert-message'});

  alertDiv.append('<a href="#" class="close" data-dismiss="alert">&times;</a>');
  alertDiv.append('<span class="glyphicon glyphicon-exclamation-sign" aria-hidden="true"></span>');

  // prepend a space to separate the message from the '!' icon
  alertDiv.append(' '+message);

  // prepend the "Need help" message
  if (severity == 'warning' || severity == 'danger'){
    alertDiv.append('<p style="text-align:center">Need help? Send us an <a href="mailto:qiita.help@gmail.com">email</a>.</p>');
  }

  if ($(".topfloat")[0]){
    $( ".topfloat" ).children().prepend(alertDiv);
  } else {
    $('#template-content').prepend(alertDiv);
  }

  if(timeout > 0) {
   if (timeoutHandleForBoostrapAlert != null) {
     window.clearTimeout(timeoutHandleForBoostrapAlert);
   }
   timeoutHandleForBoostrapAlert = window.setTimeout(function() {
     $('#alert-message').remove();
     timeoutHandleForBoostrapAlert = null;
   }, timeout);
  }
}


/*
 * format_extra_info_processing_jobs will add new rows to the study lists
 *
 * @param message: data, the original data object for the row
 *     0: blank +/- button
 *     1: heartbeat
 *     2: name
 *     3: status
 *     4: step
 *     5: id
 *     6: params
 *     7: processing_job_workflow_id
 *
 */

function format_extra_info_processing_jobs ( data ) {

    let row = '<table cellpadding="5" cellspacing="0" border="0" style="padding-left:50px;">'+
                '<tr>'+
                    '<td><b>ID:</b></td>'+
                    '<td>'+ data[5] +'</td>'+
                '</tr>'+
                '<tr>'+
                    '<td colspan="2"><h5>Parameters:</h5>'+ data[6] +'</td>'+
                '</tr>';
    row += '</table>';

    return row
}

/*
 * show_hide toggles visibility for the given div
 *
 * @param message: div, the div to toggle visibility
 *
 */

function show_hide(div) {
	$('#' + div).toggle();
}

/*
 * delete_analysis will delete an analysis
 *
 * @param aname: The name of the analysis to delete
 * @param analysis_id: The id of the analysis to delete
 *
 */

function delete_analysis(aname, analysis_id) {
  if (confirm('Are you sure you want to delete analysis: ' + aname + '?')) {
    var form = $("<form>")
    .attr("action", window.location.href)
    .attr("method", "post")
    .append($("<input>")
    .attr("type", "hidden")
    .attr("name", "analysis_id")
    .attr("value", analysis_id))
    .append($("<input>")
    .attr("type", "hidden")
    .attr("name", "action")
    .attr("value", "delete_analysis"));
    $("body").append(form);
    form.submit();
  }
}

/*
 * send_samples_to_analysis send the selected samples for the given artifact ids to analysis
 *
 * @param button: the button object that triggered this request
 * @param aids: A list of artifact ids to add
 *
 * Note that we have a list of artifact ids cause the user can select one single
 * artifact to add or all study artifacts
 */
function send_samples_to_analysis(button, aids, samples = null) {
  button.value = 'Adding';
  button.disabled = true;
  $(button).addClass("btn-info");
  bootstrapAlert('We are adding ' + aids.length + ' artifact(s) to the analysis. This ' +
                 'might take some time based on the number of samples on each artifact.', "warning", 10000);
  if (samples === null) {
    $.get('/artifact/samples/', {ids:aids})
      .done(function ( data ) {
        if (data['status']=='success') {
          qiita_websocket.send('sel', data['data']);
          button.value = 'Added';
          $(button).removeClass("btn-info");
        } else {
          bootstrapAlert('ERROR: ' + data['msg'], "danger");
          button.value = 'There was an error, scroll up to see it';
          button.disabled = false;
          $(button).addClass("btn-danger");
        }
    });
  } else {
    $.each(aids, function(i, aid) {
      var to_send = {};
      to_send[aid] = samples.split(',');
      qiita_websocket.send('sel', to_send);
    });
    button.value = 'Added';
    $(button).removeClass("btn-info");
  }
}

/**
 *
 * Function to update the name of an artifact
 *
 * @param portal_dir: string. The portal that qiita is running under
 * @param artifact_id: int. The artifact to be changed
 * @param new_name: string. The new artifact name
 * @param on_success_func: function. Function to execute when the name has been
 *        successfully updated
 *
 */
function change_artifact_name(portal_dir, artifact_id, new_name, on_success_func) {
  $.ajax({
    url: portal_dir + '/artifact/' + artifact_id + '/',
    type: 'PATCH',
    data: {'op': 'replace', 'path': '/name/', 'value': new_name},
    success: on_success_func,
    error: function(object, status, error_msg) {
      // Something went wrong, show the message
      bootstrapAlert("Error changing artifact name: " + error_msg, "danger");
    }
  });
}

/**
 * Taken from https://goo.gl/KkQ1S4
 *
 * Original script information:
 * @author Daniel McDonald
 * @copyright Copyright 2014, biocore
 * @credits Daniel McDonald, Joshua Shorenstein, Jose Navas
 * @license BSD
 * @version 0.1.0-dev
 * @maintainer Daniel McDonald
 * @email mcdonadt@colorado.edu
 * @status Development
 *
 *
 * @name qiita_websocket
 *
 * @class manages WebSocket for job information
 *
 */

var qiita_websocket = new function () {
    var
      /* the server end of the websocket */
      host = null,
      /* the websocket */
      ws = null,

      /* registered callbacks */
      callbacks = {},

      /* the encode and decode methods used for communication */
      encode = JSON.stringify,
      decode = JSON.parse;

    /**
     *
     * Registers a callback method for a given action
     *
     * @param {action} The associated action verb, str.
     * @param {func} The associated function, function. This function must
     * accept an object. Any return is ignored.
     *
     */
    this.add_callback = function(action, func) { callbacks[action] = func; };

    /**
     *
     * Packages data into an object, and passes an encoded version of the
     * object to the websocket.
     *
     * @param {action} The associated action to send, str.
     * @param {data} The data to send, str or Array of str.
     */
    this.send = function(action, data) {
        to_send = {};
        to_send[action] = data;
        ws.send(encode(to_send));
    };

    /**
     *
     * Verify the browser supports websockets, and if so, initialize the
     * websocket. On construction, this method will send a message over the
     * socket to get all known job information associated with this client.
     *
     * @param {host} The URL for the websocket, minus the ws:// header, or null
     * to use the default qiita_websocket-ws.
     * @param {on_close} Optional function for action when websocket is closed.
     * @param {on_error} Optional function for action when websocket errors.
     */
    this.init = function(host, on_close, on_error) {
        if (!("WebSocket" in window)) {
            alert("Your browser does not appear to support websockets!");
            return;
        }
        //check if we need regular or secure websocket
        socket = window.location.protocol == "https:" ? 'wss://' : 'ws://';
        ws = new WebSocket(socket + host);

        // retrive all messages
        var on_open_message = [];

        ws.onopen = function(){};
        ws.onclose = on_close;
        ws.onerror = on_error;

        ws.onmessage = function(evt) {
            message = decode(evt.data);
            for(var action in message) {
                if(action in callbacks) {
                    callbacks[action](message[action]);
                }
            }
        };
    };
};

function error(evt) {
  $('#search-error').html("<b>Server communication error. Sample selection will not be recorded. Please try again later.</b>");
}

function show_alert(data) {
  bootstrapAlert(data + ' samples selected.', "success", 10000);
  $('#dflt-sel-info').css('color', 'rgb(0, 160, 0)');
  updateSelectedSamplesMenu(function(){
    // Show the dropdown menu
    $('#selected-samples-dropdown-menu').addClass('custom-dropdown-menu');
    // Hide it after 3 seconds
    setTimeout(function() { $('#selected-samples-dropdown-menu').removeClass('custom-dropdown-menu'); }, 3000)
  });
}

function send_children_buttons(button, aids) {
  button.disabled = true;

  $.each(aids, function(idx, aid){
    button.value = 'Adding ' + (idx + 1);
    $('#send-button-'+aid).trigger("click");
  });

  button.value = 'Added';
  $(button).removeClass("btn-info");
}

function format_biom_rows(data, row, for_study_list = true, samples = null) {
  var proc_data_table = '<table class="table" cellpadding="0" cellspacing="0" border="0" style="padding-left:0px;width:95%">';
  var processing_method = {};
  proc_data_table += '<tr>';
  if (for_study_list) {
    proc_data_table += '<th></th>';
    proc_data_table += '<th>Artifacts</th>';
  }
  proc_data_table += '<th>Processing method</th>';
  if (for_study_list) {
    proc_data_table += '<th>Data type</th>';
  }
  proc_data_table += '</tr>';

  // grouping by processing_method, data_type and parameters
  $.each(data, function (idx, info) {
    // ignore the artifacts that were generated with software that is deprecated
    if (!info['deprecated']) {
      if (typeof info !== 'string' && !(info instanceof String)) {
        var algorithm = info.algorithm;
        if (!(algorithm in processing_method)) {
          processing_method[algorithm] = {};
        }

        var data_type = info.data_type + ' (' + info.target_subfragment.join(', ') + ')';
        if (!(data_type in processing_method[algorithm])) {
          processing_method[algorithm][data_type] = [];
        }
        processing_method[algorithm][data_type].push(info);
      }
    }
  });

  // creating rows
  $.each(Object.keys(processing_method).sort(), function (idx, pm) {
    var data_types = processing_method[pm];
    $.each(data_types, function (dt, artifacts) {
      proc_data_table += '<tr>';

      if (for_study_list) {
        var artifact_to_send = [];
        $.each(artifacts, function (idx, a) {
          var aid = a.artifact_id;
          artifact_to_send.push(aid);
        });
        var artifact_to_send_name = artifact_to_send.join('');
        proc_data_table += '<td>';
        proc_data_table += '<input type="button" class="btn btn-sm" value="Add all" onclick="send_children_buttons(this, [' + artifact_to_send + '])"></td>';
        proc_data_table += '<td>' +
          '<button class="btn btn-secondary btn-sm" data-toggle="collapse" data-target="#aids-' + artifact_to_send_name + '">' +
            'Per Artifact (' + artifacts.length + ')' +
          '</button>' + '</td>';
      }
      proc_data_table += '<td>' + pm + '</td>';
      if (for_study_list) {
        proc_data_table += '<td>' + dt + '</td>';
      }

      proc_data_table += '</tr>';
      if (for_study_list) {
        proc_data_table += '<tr id="aids-' + artifact_to_send_name + '" class="collapse">' +
          '<td></td>' +
          '<td colspan="4">' +
            '<table class="table table-striped table-bordered">' +
              '<thead class="thead-default">' +
                '<tr>' +
                  '<th></th>' +
                  '<th>Name</th>' +
                  '<th>Samples in Prep Info</th>' +
                  '<th>Files</th>' +
                '</tr>' +
              '</thead>' +
              '<tbody>';
          $.each(artifacts, function(idx, a){
            var aid = a.artifact_id;
            proc_data_table += '<tr>';
            proc_data_table += '<td><input type="button" id="send-button-' + aid + '" class="btn btn-sm" value="Add" onclick="send_samples_to_analysis(this, [' + aid + ']';
            if (samples === null) {
              proc_data_table += ')"></td>';
            } else {
              proc_data_table += ", '" + samples[aid].join(',') + "'" + ')"></td>';
            }
            proc_data_table += '<td>' + a.name + ' (' + aid + ' - ' + a.timestamp.split('.')[0] + ')</td>';
            proc_data_table += '<td>' + a.prep_samples + '</td>';
            proc_data_table += '<td><small>' + a.files.join('<br/>')  + '</small></td>';
            proc_data_table += '</tr>';
          });
        proc_data_table += '</tbody>' + '</table>';
        proc_data_table += '</td>' + '</tr>';
      }
    });
  });

  proc_data_table += '</table>';
  return proc_data_table;
}

function generate_private_download_link(artifact_id){
  $.ajax({
    url: "/private_download/" + artifact_id,
    method: 'POST',
    success: function(response){
      var newLink = $('<a>',{
        text: response.url,
        title: response.url,
        href: response.url
      });
      $('#privateDownloadText').text('Link will expire in 7 days');
      $('#privateDownloadText').append('<br/>')
      $('#privateDownloadText').append(newLink)
      $('#privateDownloadLink').collapse('show')
  },
  error: function(resp){
    $('#downloadLinkText').text('Failed to Generate Download Link');
    $('#privateDownloadLink').collapse('show')
  }});
}
