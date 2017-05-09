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
  // Clear the previous alert - so they don't keep stacking on top of each other
  $('#bootstrap-alert').alert('close');

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

  $('#qiita-main').prepend(alertDiv);

  if(timeout > 0) {
   if (timeoutHandleForBoostrapAlert != null) {
     window.clearTimeout(timeoutHandleForBoostrapAlert);
   }
   timeoutHandleForBoostrapAlert = window.setTimeout(function() {
     $('#alert-message').alert('close');
     timeoutHandleForBoostrapAlert = null;
   }, timeout);
  }
}

function format_extra_info_processing_jobs ( data ) {
    // `data` is the original data object for the row
    // 0: blank +/- button
    // 1: heartbeat
    // 2: name
    // 3: status
    // 4: step
    // 5: id
    // 6: params
    // 7: processing_job_workflow_id

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


function show_hide(div) {
	$('#' + div).toggle();
}

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

function send_samples_to_moi(aids, samples) {
  bootstrapAlert('We are adding ' + aids.length + ' artifact(s) to the analysis. This ' +
                 'might take some time based on the number of samples on each artifact.', "warning", 10000);

  if (typeof samples === 'undefined') {
    $.get('/artifact/samples/', {ids:aids})
      .done(function ( data ) {
        if (data['status']=='success') {
          moi.send('sel', data['data']);
        } else {
          bootstrapAlert('ERROR: ' + data['msg'], "danger", 10000);
        }
    });
  } else {
    var data = {}
    data[aids[0]] = samples
    moi.send('sel', data);
  }
}

function redbiom_send_to_moi(aid, row) {
  var row_data = $('#redbiom-table').dataTable().fnGetData(row);
  send_samples_to_moi([aid], row_data.samples);
}

function sel_study(name, row) {
  var row_data = $('#'+name).dataTable().fnGetData(row);
  var aids = []

  for(var i=0;i<row_data.proc_data_info.length;i++){
    aids.push(row_data['proc_data_info'][i]['pid']);
  }
  send_samples_to_moi(aids);
}

function sel_proc_data(aid) {
  send_samples_to_moi([aid]);
}

function remove_pd_from_html(data) {
    pid = data.proc_data;
    sid = data.sid;
    $('#proc' + pid).remove();
    $('#proc' + pid + '-samples').remove();
    // remove study if all proc data removed
    if($('#study'+ sid + '-table tbody').children().length === 1) { $('#study'+sid).remove(); }
    check_empty();
}

function check_empty() {
  if($('.row').length <= 1) {
    $('#dflt-sel-info').removeAttr('style');
    $('.topfloat').hide();
    $('#no-selected').show();
  }
}

function remove_sample_from_html(data) {
    pid = data.proc_data;
    sample = data.samples[0];
    sid = data.sid;
    document.getElementById(pid + '@' + sample).remove();
    //decriment sample count for pid
    var count = $('#proc' + pid + '-sample-count');
    count.text(parseInt(count.text(), 10) - 1);
    // remove proc data if all samples removed
    if($('#proc' + pid + '-samples-table tbody').children().length === 0) { $('#proc'+pid).remove(); $('#proc' + pid + '-samples').remove(); }
    // remove study if all proc data removed
    if($('#study'+ sid + '-table tbody').children().length === 1) { $('#study'+sid).remove(); }
    check_empty();
}

function clear_from_html(data) {
  $.each($('.row'), function(index, value) { value.remove(); });
  check_empty();
}

function error(evt) {
  $('#ws-error').html("<b>Server communication error. Sample removal will not be recorded. Please try again later.</b>");
};

function show_alert(data) {
  bootstrapAlert(data + ' samples selected.', "success", 10000);
   $('#dflt-sel-info').css('color', 'rgb(0, 160, 0)');
}
