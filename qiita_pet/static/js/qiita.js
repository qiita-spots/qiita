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

  $('#template-content').prepend(alertDiv);

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
    if (data[7] !== '' && data[3] === 'in_construction') {
      row += '<tr>'+
                '<td colspan="2">'+
                  '<button class="btn btn-danger btn-sm" onclick="remove_job(\''+ data[5] + "', '" + data[7] +'\');">'+
                  '<span class="glyphicon glyphicon-trash"></span></button>'+
                '</td>'
             '</tr>';
    }
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
 * show_hide_process_list will toggle the process/job listing visibility
 */

function show_hide_process_list() {
  if ($("#qiita-main").width() == $("#qiita-main").parent().width()) {
    // let's update the job list
    processing_jobs_vue.update_processing_job_data();
    $("#qiita-main").width("76%");
    $("#user-studies-table").width("76%");
    $("#studies-table").width("76%");
    $("#qiita-processing").width("24%");
    $("#qiita-processing").show();
  } else {
    $("#qiita-main").width("100%");
    $("#user-studies-table").width("100%");
    $("#studies-table").width("100%");
    $("#qiita-processing").width("0%");
    $("#qiita-processing").hide();
  }
}

/*
 * send_samples_to_analysis send the selected samples for the given artifact ids to analysis
 *
 * @param aids: A list of artifact ids to add
 * @param samples: The ids of the samples to add
 *
 * Note that we have a list of artifact ids cause the user can select one single
 * artifact to add or all study artifacts
 */
function send_samples_to_analysis(button, aids) {
  button.value = 'Adding';
  button.disabled = true;
  $(button).addClass("btn-info");
  bootstrapAlert('We are adding ' + aids.length + ' artifact(s) to the analysis. This ' +
                 'might take some time based on the number of samples on each artifact.', "warning", 10000);
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
}

/**
 * Draw the artifact + jobs processing graph
 *
 * Draws a vis.Network graph in the given target div with the network
 * information stored in nodes and and edges
 *
 * @param nodes: list of {id: str, label: str, group: {'artifact', 'job'}}
 *  The node information. Id is the unique id of the node (artifact or job),
 *  label is the name to show under the node and group is the type of node
 * @param edges: list of {from: str, to: str, arrows: 'to'}
 *  The connectivity information in the graph. from and to are the nodes of
 *  origin and destination of the edge, respectivelly.
 * @param target: str. The id of the target div to draw the graph
 * @param artifactFunc: function. The function to execute when the user
 *  clicks on a node of group 'artifact'. It should accept only 1 parameter
 *  which is the artifact (node) id
 * @param jobFunc: function. The function to execute when the user clicks on
 *  a node of group 'job'. It should accept only 1 parameter which is the
 *  job (node) id
 *
 */
function draw_processing_graph(nodes, edges, target, artifactFunc, jobFunc) {
  var container = document.getElementById(target);
  container.innerHTML = "";

  var nodes = new vis.DataSet(nodes);
  var edges = new vis.DataSet(edges);
  var data = {
    nodes: nodes,
    edges: edges
  };
  var options = {
    clickToUse: true,
    nodes: {
      shape: 'dot',
      font: {
        size: 16,
        color: '#000000'
      },
      size: 13,
      borderWidth: 2,
    },
    edges: {
      color: 'grey'
    },
    layout: {
      hierarchical: {
        direction: "LR",
        sortMethod: "directed",
        levelSeparation: 260
      }
    },
    interaction: {
      dragNodes: false,
      dragView: true,
      zoomView: true,
      selectConnectedEdges: true,
      navigationButtons: true,
      keyboard: false
    },
    groups: {
      jobs: {
        color: '#FF9152'
      },
      artifact: {
        color: '#FFFFFF'
      }
    }
  };

  var network = new vis.Network(container, data, options);
  network.on("click", function (properties) {
    var ids = properties.nodes;
    if (ids.length == 0) {
      return
    }
    // [0] cause only users can only select 1 node
    var clickedNode = nodes.get(ids)[0];
    var element_id = ids[0];
    if (clickedNode.group == 'artifact') {
      artifactFunc(element_id);
    } else {
      jobFunc(element_id);
    }
  });
};


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
}

function format_biom_rows(data, row) {
  var proc_data_table = '<table class="table" cellpadding="0" cellspacing="0" border="0" style="padding-left:0px;width:95%">';
  proc_data_table += '<tr>';
  proc_data_table += '<th>Name</th>';
  proc_data_table += '<th>Processing method</th>';
  proc_data_table += '<th>Parameters</th>';
  proc_data_table += '<th>Files</th>';
  proc_data_table += '</tr>';
  $.each(data, function (idx, info) {
    if (typeof info !== 'string' && !(info instanceof String)) {
      proc_data_table += '<tr>';
      proc_data_table += '<td>' + info.name + ' (' + info.artifact_id + ' - ' + info.timestamp.split('.')[0] + ')</td>';
      proc_data_table += '<td>' + info.algorithm + '</td>';
      var params = '';
      for (var key in info.parameters) {
        params += '<i>' + key + '</i>: ' + info.parameters[key] + '<br/>';
      }
      proc_data_table += '<td><small>' + params + '</small></td>';
      proc_data_table += '<td><small>' + info.files.join('<br/>')  + '</small></td>';
      proc_data_table += '</tr>';
    }
  });

  proc_data_table += '</table>';
  return proc_data_table;
}
