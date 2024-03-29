// This global variable holds the Vue object - it is needed to be able to
// trigger some functions from other elements
var processingNetwork = null;


/**
 *
 * Function to format the node labels so they don't overlap
 *
 * @param label str The node label
 *
 **/
function formatNodeLabel(label) {
  // After trying different values, 35 looks like a good value that will not make
  // the labels overlap in the network.
  var limit = 35;
  // Split the input string by the space characters
  var labelArray = label.split(' ');
  // Variable holding the new label
  var newLabel = labelArray[0];
  var aux;
  var lastNewLineIdx = 0;
  // Note that the for loop starts with 1 because we have already used the
  // first word
  for (var i = 1; i < labelArray.length; i++) {
    aux = newLabel + ' ' + labelArray[i];
    if (aux.substr(lastNewLineIdx).length > limit) {
      // We need to split the label here
      lastNewLineIdx = newLabel.length;
      newLabel = newLabel + '\n' + labelArray[i];
    } else {
      newLabel = newLabel + ' ' + labelArray[i];
    }
  }
  return newLabel;
};

/**
 *
 * Toggle the graph view
 *
 * Show/hide the graph div and update GUI accordingly
 *
 **/
function toggleNetworkGraph() {
  if($("#processing-network-div").css('display') == 'none' ) {
    // if we are displayin the waiting page, do not show the instructions
    if (!$("#processing-network-div").html().includes('waiting')){
      $("#processing-network-instructions-div").show();
    }
    $("#processing-network-div").show();
    $("#show-hide-network-btn").text("Hide");
  } else {
    $("#processing-network-instructions-div").hide();
    $("#processing-network-div").hide();
    $("#show-hide-network-btn").text("Show");
  }
};

function edge_sorting(a, b){
  let order = 1;
  if (a.data.source > b.data.source){
    order = -1;
  } else if ((a.data.source === b.data.source) && (a.data.target < b.data.target)){
    order = -1;
  }
  return order;
}

Vue.component('processing-graph', {
  template: '<div class="row">' +
              '<div class="row" id="network-header-div">' +
                '<div class="col-md-12">' +
                  // Processing Network header and Show/hide button
                  '<div class="row">' +
                    '<div class="col-md-2">' +
                      '<h4>Processing network</h4>' +
                    '</div>' +
                    '<div class="col-md-1">' +
                      '<a class="btn btn-info form-control" id="show-hide-network-btn" onclick="toggleNetworkGraph();">Hide</a>' +
                    '</div>' +
                  '</div>' +
                  // Run workflow button
                  '<div class="row" id="run-btn-div">' +
                    '<div class="col-md-2">' +
                      '<h4><span class="blinking-message">Start workflow:</h4></span>' +
                    '</div>' +
                    '<div class="col-md-2">' +
                      '<a class="btn btn-success form-control" id="run-btn"><span class="glyphicon glyphicon-play"></span> Run</a>' +
                    '</div>' +
                  '</div>' +
                  '<div class="row" id="processing-network-instructions-div">' +
                    '<div class="col-md-12">' +
                      '<b>Click on the graph to navigate through it. Click circles for more information. This graph will refresh in <span id="countdown-span"></span> seconds or reload <a href="#" id="refresh-now-link">now</a><br/><span id="circle-explanation"></span></b>' +
                    '</div>' +
                  '</div>' +
                '</div>' +
              '</div>' +
              '<div class="row">' +
                '<div class="col-md-12">' +
                  '<div class="col-md-12 graph" style="width:90%" id="processing-network-div">' +
                '</div>' +
              '</div>' +
              '<div class="row">' +
                '<div class="col-md-12" style="width:90%" id="processing-job-div">' +
                '</div>' +
              '</div>' +
              '<div class="row">' +
                '<div class="col-md-12" style="width:90%; padding-left: 30px" id="processing-results">' +
                '</div>' +
              '</div>' +
            '</div>',
  props: ['portal', 'graph-endpoint', 'jobs-endpoint', 'no-init-jobs-callback', 'is-analysis-pipeline', 'element-id'],
  methods: {
    /**
     *
     * Resets the zoom view of the graph
     *
     **/
    resetZoom: function () {
      let vm = this;
      if (vm.network !== undefined && vm.network !== null) {
        vm.network.fit();
      }
    },

    /**
     *
     * Cleans up the current object
     *
     **/
    destroy: function() {
      let vm = this;
      clearInterval(vm.interval);
      if (vm.network !== undefined) {
        vm.network.destroy();
      }
    },

    /**
     *
     * Updates the status of those jobs in a non-terminal state
     *
     **/
    update_job_status: function() {
      let vm = this;
      var requests = [];
      var jobId, jobStatus, jobNode;
      var needsUpdate = false;

      if (vm.runningJobs.length > 0) {
        $.each(vm.runningJobs, function(index, value) {
          requests.push($.get(vm.portal + '/study/process/job/', {job_id: value}));
        });

        // Reset the runningJobs list, since we are going to be adding
        // the running jobs below
        vm.runningJobs = [];

        $.when.apply($, requests).then(function() {
          // The nature of arguments change based on the number of requests
          // performed. If only one request was performed, then arguments only
          // contains the output of that request. Otherwise, arguments contains
          // is a list of results
          var arg = (requests.length === 1) ? [arguments] : arguments;
          $.each(arg, function(index, value) {
            // The actual result of the call is stored in the first element of
            // the list, hence accessing with 0
            jobId = value[0]['job_id'];
            jobStatus = value[0]['job_status'];
            jobNode = vm.network.getElementById(jobId);

            if (jobNode === null) {
              // A network node does not exist for this job, this is because this
              // job is a job deleting an artifact
              if (jobStatus === 'success' || jobStatus === 'error') {
                // The jobs finished, in any of the two finishing states we need
                // to update the graph
                needsUpdate = true;
                if (jobStatus === 'error') {
                  // If the job didn't complete successfully, we need to show the
                  // error to the user
                  bootstrapAlert(value[0]['job_error'], "danger");
                }
              } else {
                // The job is still running
                vm.runningJobs.push(jobId);
              }
            } else {
              // If the job is in one of the "running" states, we add it to the runningJobs list
              if (jobStatus === 'running' || jobStatus === 'queued' || jobStatus === 'waiting') {
                vm.runningJobs.push(jobId);
              }

              if (jobNode.data('status') !== jobStatus) {
                // The status of the job changed.
                // we decide what to do based on the new status.
                if (jobStatus === 'success' || jobStatus === 'error') {
                  // If the job succeeded or failed, we need to reset the entire graph
                  // because the changes on the nodes are substantial
                  needsUpdate = true;
                } else {
                  // In this case the job changed to either 'running', 'queued' or 'waiting'. In
                  // this case, we just need to update the internal values of the nodes and the colors
                  var node_info = vm.colorScheme[jobStatus];
                  jobNode.data('color', node_info['background']);
                  jobNode.data('shape', node_info['shape']);
                }
              }
            }
          });

          if (needsUpdate) {
            // Update the entire graph if the status of the jobs require so
            vm.updateGraph();
          }
        });
      }
    },

    /**
     *
     * Deletes an artifact from the network
     *
     **/
    deleteArtifact: function(artifactId) {
      let vm = this;
      $.post(vm.portal + '/artifact/' + artifactId + '/', function(data) {
        // Clean up the div
        $("#processing-results").empty();
        // Update the artifact node to mark that it is being deleted
        var node = vm.network.getElementById(artifactId.toString());
        node.data('color', vm.colorScheme['deleting']['background']);
        node.data('shape', vm.colorScheme['deleting']['shape']);

        // Add the job to the list of jobs to check for deletion.
        vm.runningJobs.push(data.job);
      })
       .fail(function(object, status, error_msg) {
         bootstrapAlert('Error deleting artifact: ' + object.statusText.replace("\n", "<br/>"), danger);
       })
    },

    /**
     *
     * Remove a job node from the network visualization
     *
     * @param jobId str The id of the job
     *
     * This function removes the given job and its children from the
     * network visualization
     *
     **/
    removeJobNodeFromGraph: function(jobId) {
      let vm = this;
      var node = vm.network.getElementById(jobId);
      node.successors(function( d ){
        vm.network.remove(d);
      });
      vm.network.remove(node);
      if (vm.inConstructionJobs === 0) {
        $('#run-btn-div').hide();
      }
    },

    /**
     *
     * Remove a job from the workflow
     *
     * @param jobId str The id of the job to be removed
     * @param jobStatus str The status of the job to be removed
     *
     * This function executes an AJAX call to remove the given job from the
     * current workflow and updates the graph accordingly
     *
     **/
    removeJob: function(jobId, jobStatus) {
      let vm = this;
      var url, path;
      if(confirm("Are you sure you want to delete the job " + jobId + "?")) {
        if (jobStatus === 'error' || jobStatus === 'in_construction') {
          if (jobStatus === 'error') {
            url = '/study/process/job/';
            path = jobId;
          } else if (jobStatus === 'in_construction') {
            url = '/study/process/workflow/';
            path = '/' + vm.workflowId + '/' + jobId;
          }
          $.ajax({
            url: vm.portal + url,
            type: 'PATCH',
            data: {'op': 'remove', 'path': path},
            success: function(data) {
              if(data.status == 'error') {
                bootstrapAlert(data.message, "danger");
              }
              else {
                vm.removeJobNodeFromGraph(jobId);
                $("#processing-results").empty();
              }
            }
          });
        } else {
          // With the current code we should never get to this else, but better
          // to throw an error just in case
          throw "Job " + jobId + " can't be deleted. Current status: " + jobStatus;
        }
      }
    },

    /**
     *
     * Submit the current workflow for execution
     *
     * This function executes an AJAX call to submit the current workflow
     * for execution
     *
     */
    runWorkflow: function() {
      $('#run-btn').attr('disabled', true);
      $('#run-btn').html('<span class="glyphicon glyphicon-stop"></span> Submitting');
      let vm = this;
      $.post(vm.portal + "/study/process/workflow/run/", {workflow_id: vm.workflowId}, function(data){
        bootstrapAlert("Workflow " + vm.workflowId + " submitted", "success");
        $('#run-btn-div').hide();
        $("#processing-results").empty();
        vm.updateGraph();
      })
        .fail(function(object, status, error_msg) {
          bootstrapAlert("Error submitting workflow: " + object.statusText, "danger");
        })
        .always(function() {
          // return button to regular state
          $('#run-btn').attr('disabled', false);
          $('#run-btn').html('<span class="glyphicon glyphicon-play"></span> Run');
        });
    },

    /**
     *
     * Populates the target div with the job information
     *
     * @param jobId: str. The job id
     *
     **/
    populateContentJob: function(jobId) {
      let vm = this;
      var $rowDiv, $colDiv;
      // Put the loading gif in the div
      show_loading("processing-results");
      $.get(vm.portal + '/study/process/job/', {job_id: jobId}, function(data){
        $("#processing-results").empty();

        // Create the header of the page
        var h = $("<h3>").text('Job ' + data['job_id'] + ' [' + data['job_external_id'] + '] ').appendTo("#processing-results");

        // Only add the delete job button if the job is "in_construction"
        // or "error"
        if (data['job_status'] === 'in_construction' || data['job_status'] === 'error') {
          var deleteBtn = $("<a>").addClass("btn btn-danger btn-sm").appendTo(h);
          $('<span class="glyphicon glyphicon-trash"></span>').appendTo(deleteBtn);
          deleteBtn.append(' Delete');
          var jId = data['job_id'];
          var jStatus = data['job_status'];
          deleteBtn.on('click', function() {vm.removeJob(jId, jStatus);});
        }

        // Create a list that contains the contents of each row. This way we
        // reduce code duplication when creation the row HTML elements
        var rowsContent = [];
        // Add the Command information
        rowsContent.push(['Command:', data['command'] + ' (' + data['software'] + ' ' + data['software_version'] + ')<br/>' + data['command_description']]);
        // Add the status
        rowsContent.push(['Status:', data['job_status'].replace('_', ' ')]);

        // Add the job step
        if (data['job_step'] !== null && data['job_status'] !== 'success') {
          rowsContent.push(['Current step:', data['job_step']]);
        }

        if (data['job_status'] === 'error' && data['job_error'] !== null) {
          // based on https://stackoverflow.com/a/14129989
          rowsContent.push(['Error message:', $('<div>').text(data['job_error']).html()]);
        }

        // Create the DOM elements to add the rows content
        for (var row of rowsContent) {
          $rowDiv = $('<div>').addClass('row').addClass('form-group').appendTo("#processing-results");
          $rowLabel = $('<div>').addClass('col-sm-4').appendTo($rowDiv);
          $('<label>').addClass('col-form-label').text(row[0]).appendTo($rowLabel);
          $('<div>').addClass('col-sm-8').appendTo($rowDiv).html(row[1]);
        }

        $("#processing-results").append($("<h4>").text('Job parameters:'));

        for(var key in data.job_parameters){
          if (key.startsWith("qp-hide")) {
            continue;
          }
          $rowDiv = $('<div>').addClass('row').addClass('form-group').appendTo("#processing-results");
          $rowLabel = $('<div>').addClass('col-sm-4').appendTo($rowDiv);
          $('<label>').addClass('col-form-label').text(key + ':').appendTo($rowLabel);
          $('<div>').addClass('col-sm-8').appendTo($rowDiv).html(data.job_parameters[key]);
        }
      })
        .fail(function(object, status, error_msg) {
          $("#processing-results").html("Error loading artifact information: " + status + " " + error_msg);
        }
      );
    },

    /**
     * Populates the target div with the artifact information
     *
     * @param artifactId: int. The artifact id
     *
     */
    populateContentArtifact: function(artifactId) {
      let vm = this;
      // Put the loading gif in the div
      show_loading('processing-results');
      $.get(vm.portal + '/artifact/' + artifactId + '/summary/', function(data){
        $("#processing-results").html(data);
      })
        .fail(function(object, status, error_msg) {
          $("#processing-results").html("Error loading artifact information: " + status + " " + object.statusText);
        }
      );
    },

    /**
     *
     * Load the GUI for a given command parameter
     *
     * @param p_name str the name of the parameter
     * @param param_info object the information of the parameter
     * @param sel_artifacts_info object with the information of the currently selected artifacts
     * @param target DOM div to add the parameter gui
     * @param dflt_val object with the default value to use for the given parameter
     *
     * This function generates the needed GUI specific to the given parameter type
     *
     **/
    loadParameterGUI: function(p_name, param_info, sel_artifacts_info, target, dflt_val) {
      let vm = this;
      // Create the parameter interface
      var $rowDiv = $('<div>').addClass('row').addClass('form-group').appendTo(target);
      // Replace the '_' by ' ' in the parameter name for readability
      $('<label>').addClass('col-sm-2').addClass('col-form-label').text(p_name.replace('_', ' ') + ': ').appendTo($rowDiv).attr('for', p_name);
      var $colDiv = $('<div>').addClass('col-sm-3').appendTo($rowDiv);

      var p_type = param_info[0];
      var allowed_types = param_info[1];
      var $inp;

      if (p_type == 'artifact' || p_type.startsWith('choice') || p_type.startsWith('mchoice')) {
        // The parameter type is an artifact or choice, the input type is a dropdown
        $inp = $('<select>');
        // show a dropdown menu with the
        var options = [];
        if (p_type.startsWith('choice') || p_type.startsWith('mchoice')) {
          $.each(JSON.parse(p_type.split(':')[1]), function (idx, val) { options.push([val, val]); });

          if (p_type.startsWith('mchoice')) {
            $inp.attr('multiple', true);
          }
        }
        else {
          // available artifacts of the given type
          for(var key in sel_artifacts_info) {
             if(allowed_types.indexOf(sel_artifacts_info[key].type) !== -1) {
               options.push([key, sel_artifacts_info[key].name]);
             }
          }
        }

        options.sort(function(a, b){return a[0].localeCompare(b[0], 'en', {'sensitivity': 'base'});});
        $.each(options, function(idx, val) {
          $inp.append($("<option>").attr('value', val[0]).text(val[1]));
        });
      }
      else {
        // The rest of parameter types are represented with an input
        $inp = $('<input>');
        // It just changes the type of input
        if (p_name.startsWith("qp-hide")) {
          // adding the hide attributes
          $inp.attr('type', 'hidden');
          $rowDiv.css('display', 'none');
        }
        else if (p_type == 'integer') {
          // For the integer type, show an input of type number
          $inp.attr('type', 'number');
        }
        else if (p_type == 'float') {
          // For the float type, show an input of type number, with a step of 0.001
          $inp.attr('type', 'number').attr('step', 0.001);
        }
        else if (p_type == 'string') {
          // For the float type, show an input of type text
          $inp.attr('type', 'text');
        }
        else if (p_type == 'boolean') {
          // For the boolean type, show an input of type checkbox
          $inp.attr('type', 'checkbox');
        }
        else {
          bootstrapAlert("Error: Parameter type (" + p_type + ") not recognized. Please, take a screenshot and <a href='mailto:qiita.help@gmail.com'>contact us</a>", "danger");
        }
      }

      if (dflt_val !== undefined) {
        if (p_type == 'boolean') {
          // The boolean type works differently than the others, so we needed
          // to special case it here.
          if (dflt_val !== 'false' && dflt_val !== false) {
            $inp.prop('checked', true);
          } else {
            $inp.prop('checked', false);
          }
        }
        else {
          $inp.val(dflt_val);
        }
        if (!vm.isAnalysisPipeline) {
          $inp.prop('disabled', true);
        }
        $inp.addClass('optional-parameter');
      }
      else {
        $inp.addClass('required-parameter');
      }

      $inp.appendTo($colDiv).attr('id', p_name).attr('name', p_name).addClass('form-control');
    },

    /**
     *
     * Load the GUI for the options of a command
     *
     * @param cmd_id int the command to load the options from
     * @param sel_artifacts_info object with the information of the currently selected artifacts
     *
     * This function executes an AJAX call to retrieve the information about the
     * options of the given command and generates the GUI to present those options
     * to the user
     *
     */
    loadCommandOptions: function(cmd_id, sel_artifacts_info) {
      let vm = this;
      // [0] cause there is only one
      let artifact_id = Object.keys(sel_artifacts_info)[0];
      $.get(vm.portal + '/study/process/commands/options/', {command_id: cmd_id, artifact_id: artifact_id})
        .done(function(data){
            // Put first the required parameters
            $("#cmd-opts-div").append($('<h4>').text('Required parameters:'));
            var keys = Object.keys(data.req_options).sort(function(a, b){return a.localeCompare(b, 'en', {'sensitivity': 'base'});});

            // adding extra artifacts to sel_artifacts_info so they are added to the GUI
            $.each(data.extra_artifacts, function(artifact_type, artifacts) {
              $.each(artifacts, function(index, adata) {
                sel_artifacts_info[adata[0]] = {'type': artifact_type, 'name': adata[1] + ' [' + adata[0] + ']'}
              });
            });

            for (var i = 0; i < keys.length; i++) {
              var key = keys[i];
              vm.loadParameterGUI(key, data.req_options[key], sel_artifacts_info, $("#cmd-opts-div"));
            }

            // Put a dropdown menu to choose the default parameter set
            $("#cmd-opts-div").append($('<h4>').text('Optional parameters:'));
            var $rowDiv = $('<div>').addClass('row').addClass('form-group').appendTo("#cmd-opts-div");
            $('<label>').addClass('col-sm-2').addClass('col-form-label').text('Parameter set:').appendTo($rowDiv).attr('for', 'params-sel');
            var $colDiv = $('<div>').addClass('col-sm-3').appendTo($rowDiv);
            var sel = $('<select>').appendTo($colDiv).attr('id', 'params-sel').attr('name', 'params-sel').addClass('form-control').attr('placeholder', 'Choose parameter set...');
            sel.append($("<option>").attr('value', "").text("Choose parameter set...").prop('disabled', true).prop('selected', true));
            var options = data.options;
            options.sort(function(a, b) {return a.name.localeCompare(b.name, 'en', {'sensitivity': 'base'});} );
            for(var i=0; i<options.length; i++) {
              sel.append($("<option>").attr('value', options[i].id).attr('data-vals', JSON.stringify(options[i].values)).text(options[i].name));
            }
            $("<div>").appendTo("#cmd-opts-div").attr('id', 'opt-vals-div').attr('name', 'opt-vals-div');

            sel.change(function(){
              var v = $("#params-sel").val();
              $("#opt-vals-div").empty();
              if (v !== "") {
                if (!vm.isAnalysisPipeline) {
                  $("#opt-vals-div").append($('<label>').text('Note: changing default parameter values not allowed'));
                }
                // Get the parameter set values that the user selected
                var opt_vals = JSON.parse($("#params-sel option[value='" + v + "']").attr("data-vals"));
                var keys = Object.keys(data.opt_options).sort(function(a, b){return a.localeCompare(b, 'en', {'sensitivity': 'base'});});
                for (var i = 0; i < keys.length; i++) {
                  var key = keys[i];
                  vm.loadParameterGUI(key, data.opt_options[key], sel_artifacts_info, $("#opt-vals-div"), opt_vals[key]);
                }
                $("#add-cmd-btn-div").show();
              }
              else {
                $("#add-cmd-btn-div").hide();
              }
            });

            sel.show(function(){
              // select first option if only 2 options ("Choose parameter set", "unique value")
              if ($("#params-sel option").length == 2) {
                $("#params-sel")[0].selectedIndex = 1;
                $("#params-sel").trigger("change");
              }
            });
        });
    },

    /**
     *
     * Generates the GUI for selecting the commands to apply to the given artifacts
     *
     * @param p_node str The id of the selected artifact
     *
     * This function executes an AJAX call to retrieve all the commands that can
     * process the selected artifacts. It generates the interface so the user
     * can select which command should be added to the workflow
     *
     **/
    loadArtifactType: function(p_node) {
      let vm = this;
      var sel_artifacts_info = {};
      var node, nodeIdSplit, $rowDiv, $colDiv;
      var target = $("#processing-results");

      // We need to differentiate between the artifact type nodes that are part
      // of the current in construction workflow of if the node is from a
      // previous workflow. If it is from a previous workflow, no new commands
      // can be added. This is due to assumptions done on different sections
      // of the code that are not easy to remove. The easiest way to identify
      // the type of artifact type node is by checking the job that is
      // generating this artifact type.
      p_node = String(p_node);
      nodeIdSplit = p_node.split(':');
      node = vm.network.getElementById(p_node).data();
      root = vm.network.nodes()[0].id();
      if (nodeIdSplit.length < 2 || vm.network.getElementById(nodeIdSplit[0]).data().status === 'in_construction') {
        // This means that either we are going to process a new artifact (nodeIdSplit.length < 2)
        // or that the parent job generating this artifact type node is in construction.
        // In both of this cases, we can add a new job to the workflow
        sel_artifacts_info[node.id] = {'type': node.type, 'name': node.label};
        artifact_id = nodeIdSplit.length < 2 ? node.id : node.type + ':' + root ;

        $.get(vm.portal + '/study/process/commands/', {artifact_id: artifact_id, include_analysis: vm.isAnalysisPipeline})
          .done(function (data) {
            target.empty();

            // Create the command select dropdown
            $rowDiv = $('<div>').addClass('row').addClass('form-group').appendTo(target);
            $('<label>').addClass('col-sm-2').addClass('col-form-label').text('Choose command:').appendTo($rowDiv).attr('for', 'command-sel');
            $colDiv = $('<div>').addClass('col-sm-3').appendTo($rowDiv);
            var sel = $('<select>').appendTo($colDiv).attr('id', 'command-sel').attr('name', 'command').addClass('form-control').attr('placeholder', 'Choose command...');
            sel.append($("<option>").attr('value', "").text("Choose command...").prop('disabled', true).prop('selected', true));
            var commands = data.commands;
            commands.sort(function(a, b) {return a.command.localeCompare(b.command, 'en', {'sensitivity': 'base'});} );
            for(var i=0; i<commands.length; i++) {
              if (commands[i].output.length !== 0) {
                sel.append($("<option>").attr('value', commands[i].id).text(commands[i].command));
              }
            }
            sel.change(function(event) {
              $("#cmd-opts-div").empty();
              $("#add-cmd-btn-div").hide();
              var v = $("#command-sel").val();
              if (v !== "") {
                vm.loadCommandOptions(v, sel_artifacts_info);
              }
            });

            // Create the div in which the command options will be shown
            $('<div>').appendTo(target).attr('id', 'cmd-opts-div').attr('name', 'cmd-opts-div');

            // Create the add command button - but not show it yet
            var $rowDiv = $('<div hidden>').addClass('row').addClass('form-group').appendTo(target).attr('id', 'add-cmd-btn-div').attr('name', 'add-cmd-btn-div');
            var $colDiv = $('<div>').addClass('col-sm-2').appendTo($rowDiv);
            $('<button>').appendTo($colDiv).addClass('btn btn-info').text('Add Command').click(function() {vm.addJob();});
          });
      } else {
        target.empty();
        $('<h4>').append('Future result: ' + node.label).appendTo(target);
        $rowDiv = $('<div>').addClass('row').addClass('form-group').appendTo(target);
        $('<label>').addClass('col-sm-1').addClass('col-form-label').text('Generated by:').appendTo($rowDiv);
        $colDiv = $('<div>').addClass('col-sm-3').appendTo($rowDiv).append(node.label + ' (' + nodeIdSplit[0] + ')');
        $rowDiv = $('<div>').addClass('row').addClass('form-group').appendTo(target);
        $('<label>').addClass('col-sm-1').addClass('col-form-label').text('Output name:').appendTo($rowDiv);
        $colDiv = $('<div>').addClass('col-sm-3').appendTo($rowDiv).append(nodeIdSplit[1]);
      }
    },

    /**
     *
     * Add a job node to the network visualization
     *
     * @param job_info object The information of the new job to be added
     *
     * This function adds a new job node to the network visualization, as well as
     * adding the needed children and edges between its inputs and outputs (children)
     *
     **/
    addJobNodeToGraph: function(job_info) {
      let vm = this;

      vm.new_job_info = {
        job_id: job_info.id,
        viewport: {zoom: vm.network.zoom(), pan: vm.network.pan()}
      }
      vm.updateGraph();
    },

    /**
     * Draw the artifact + jobs processing graph
     *
     * Draws a vis.Network graph in the given target div with the network
     * information stored in nodes and and edges
     *
     * @param target_details: str. The id of the target div to display the
     *  job/artifact details
     *
     */
    drawProcessingGraph: function(target_details) {
      let vm = this;
      var container = document.getElementById('processing-network-div');
      container.innerHTML = "";
      // Making sure the network is available
      $("#processing-network-div").show();
      $("#processing-network-instructions-div").show();

      var layout = {
        name: 'dagre',
        rankDir: 'LR',
        directed: true,
        nodeDimensionsIncludeLabels: true,
        nodeSep: 2,
        spacingFactor: 1.2,
        padding: 5
      };
      var style = [{
        selector: 'node',
        style: {
          'content': 'data(label)',
          'background-color': 'data(color)',
          'shape': 'data(shape)',
          'text-opacity': 0.7,
          'text-wrap': "wrap",
          'border-color': '#333',
          'border-width': '3px'
        }}, {
        selector: 'edge',
        style: {
          'curve-style': 'bezier',
          'target-arrow-shape': 'triangle'
        }}, {
        selector: 'node.highlight',
        style: {
         'border-width': '5px'
        }}, {
        selector: 'edge.highlight',
        style: {
          'line-color': '#333',
          'target-arrow-color': '#333'
        }}
      ];
      var panzoom_options =	{
        zoomOnly: true,
        sliderHandleIcon: 'fa fa-minus',
        zoomInIcon: 'fa fa-plus',
        zoomOutIcon: 'fa fa-minus',
        resetIcon: 'fa fa-expand'
      };

      // Note: we only need to sort the edges to keep the same structure of the
      //       graph; in other words, nodes order is not important
      vm.edges = vm.edges.sort(edge_sorting);

      vm.network = cytoscape({
          container: container,
          minZoom: 1e-50,
          maxZoom: 2,
          wheelSensitivity: .3,
          layout: layout, style: style,
          elements: {
            nodes: vm.nodes,
            edges: vm.edges,
          }
        });
      vm.network.panzoom(panzoom_options);
      vm.network.nodes().lock();

      vm.network.ready(function() {
        if (vm.new_job_info !== null){
          vm.network.viewport(vm.new_job_info['viewport']);
          node = vm.network.getElementById(vm.new_job_info.job_id);
          // center in the children of the new job
          vm.network.center(node.successors());
          vm.new_job_info = null;
        }
      });

      vm.network.on('tap', 'node', function (evt) {
        var target = evt.target;
        var data = target.data();
        var element_id = data.id;

        // removing all highlight classes from network and highlighting the
        // element that was just selected
        vm.network.nodes().removeClass('highlight');
        vm.network.edges().removeClass('highlight');
        target.addClass('highlight');
        target.connectedEdges().addClass('highlight');

        if (data.group === 'artifact') {
          vm.populateContentArtifact(element_id);
        } else if (data.group === 'deleting') {
          $("#processing-results").empty();
          $("#processing-results").append("<h4>This artifact is being deleted</h4>");
        } else {
          var ei = element_id.split(':');
          if (ei.length == 2) {
            vm.loadArtifactType(element_id);
          } else {
            vm.populateContentJob(element_id);
          }
        }
      });
    },

    /**
     *
     * Create a new workflow
     *
     * @param cmd_id int the command to execute on the first job of the workflow
     * @param params object the parameters of the first job of the workflow
     *
     * This function executes an AJAX call to create a new workflow by providing
     * the first job in the workflow.
     *
     **/
    createWorkflow: function(cmd_id, params) {
      let vm = this;
      $.post(vm.portal + '/study/process/workflow/', {command_id: cmd_id, params: JSON.stringify(params) })
        .done(function(data) {
          if (data.status == 'success') {
            vm.workflowId = data.workflow_id;
            vm.addJobNodeToGraph(data.job);
          }
          else {
            bootstrapAlert(data.message.replace(/\n/g, '<br/>'), "danger");
          }
        });
    },

    /**
     *
     * Adds a new job to the current workflow
     *
     * @param command_id int the command to execute on the new job
     * @param params_id int the id of the default parameter set to be used in the new job
     * @param req_params object the required parameters of the new job
     * @param opt_params obect the optional parameters of the new job
     *
     * This function formats the data correctly and executes an AJAX call to
     * create and add a new job to the current workflow
     *
     **/
    createJob: function (command_id, params_id, req_params, opt_params) {
      let vm = this;
      var value = {'dflt_params': params_id};
      var connections = {}
      var r_params = {}
      for (var param in req_params) {
        var vs = req_params[param].split(':');
        if (vs.length == 2) {
          if(!connections.hasOwnProperty(vs[0])){
            connections[vs[0]] = {};
          }
          connections[vs[0]][vs[1]] = param;
        }
        else {
          r_params[param] = req_params[param];
        }
      }
      value['connections'] = connections;
      value['req_params'] = r_params;
      value['opt_params'] = opt_params;
      $.ajax({
        url: vm.portal + '/study/process/workflow/',
        type: 'PATCH',
        data: {'op': 'add', 'path': vm.workflowId, 'value': JSON.stringify(value)},
        success: function(data) {
          if(data.status == 'error') {
            bootstrapAlert(data.message, "danger");
            window.scrollTo(0, 0);
          }
          else {
            var inputs = [];
            for(var k in req_params) {
              inputs.push(req_params[k]);
            }
            data.job.inputs = inputs;
            vm.addJobNodeToGraph(data.job);
          }
        }
      });
    },

    /**
     *
     * Adds a new job to the workflow
     *
     *
     * This function retrieves the information to add a new job to the workflow.
     * If the workflow still doesn't exist, it calls 'createWorkflow'. Otherwise
     * it calls "createJob".
     *
     **/
    addJob: function () {
      let vm = this;
      var command_id = $("#command-sel").val();
      var params_id = $("#params-sel").val();
      var params = {};
      // Collect the required parameters
      var req_params = {};
      $(".required-parameter").each( function () {
        params[this.id] = this.value;
        req_params[this.id] = this.value;
      });
      // Collect the optional parameters
      var opt_params = {};
      $(".optional-parameter").each( function () {
        var value = this.value;
        if ( $(this).attr('type') === 'checkbox' ) {
          value = this.checked;
        }
        params[this.id] = value;
        opt_params[this.id] = value;
      });
      if (vm.workflowId === null) {
        // This is the first command to be run, so the workflow still doesn't
        // exist in the system.
        vm.createWorkflow(command_id, params);
      }
      else {
        vm.createJob(command_id, params_id, req_params, opt_params);
      }

      $('#processing-results').empty();
      if (vm.inConstructionJobs === 0) {
        $('#run-btn-div').show();
      }
      vm.inConstructionJobs += 1;
    },

    /**
     *
     * This function retrieves the entire graph from Qiita and re-draws the
     * the entire graph.
     *
     **/
    updateGraph: function () {
      let vm = this;

      vm.nodes = [];
      vm.edges = [];
      vm.runningJobs = [];
      vm.inConstructionJobs = 0;
      vm.workflowId = null;

      $.get(vm.portal + vm.graphEndpoint, function(data) {
        // If there are no nodes in the graph, it means that we are waiting
        // for the jobs to generate the initial set of artifacts. Update
        // the job list
        if (data.nodes.length == 0) {
          $("#processing-network-div").hide();
          vm.checkInitialJobs();
        }
        else {
          vm.nodes = [];
          vm.edges = [];
          vm.workflowId = data.workflow;
          // The initial set of artifacts has been created! Format the graph
          // data in a way that Vis.Network likes it
          // Format edge list data
          for(var i = 0; i < data.edges.length; i++) {
            // forcing a string
            data.edges[i][0] = data.edges[i][0].toString()
            data.edges[i][1] = data.edges[i][1].toString()
            vm.edges.push({data: {source: data.edges[i][0], target: data.edges[i][1]}});
          }
          // Format node list data
          for(var i = 0; i < data.nodes.length; i++) {
            var node_info = vm.colorScheme[data.nodes[i][4]];
            if (data.artifacts_being_deleted.includes(data.nodes[i][2])) {
              data.nodes[i][0] = 'deleting'
              node_info = vm.colorScheme['deleting']
            }
            // forcing a string
            data.nodes[i][2] = data.nodes[i][2].toString()
            vm.nodes.push({data: {id: data.nodes[i][2], shape: node_info['shape'], label: formatNodeLabel(data.nodes[i][3]), type: data.nodes[i][1], group: data.nodes[i][0], color: node_info['background'], status: data.nodes[i][4]}});
            if (data.nodes[i][1] === 'job') {
              job_status = data.nodes[i][4];
              if (job_status === 'in_construction') {
                vm.inConstructionJobs += 1;
              } else if (job_status === 'running' || job_status === 'queued' || job_status === 'waiting') {
                vm.runningJobs.push(data.nodes[i][2]);
              }
            }
          }
          vm.drawProcessingGraph('processing-results');
          if (vm.inConstructionJobs > 0) {
            $('#run-btn-div').show();
          }

          // At this point we can show the graph and hide the job list
          $("#processing-network-div").show();
          $("#processing-network-instructions-div").show();
          $("#show-hide-network-btn").show();
          $("#processing-job-div").hide();
          if (vm.workflowId === null && vm.isAnalysisPipeline === false) {
            $("#add-default-workflow").show();
          } else {
            $("#add-default-workflow").hide();
          }
        }
      })
        .fail(function(object, status, error_msg) {
          // Show an error message if something wrong happen, rather than
          // leaving the spinning wheel of death in there.
          $("#processing-network-div").html("Error loading graph: " + status + " " + error_msg);
          $("#processing-network-div").show();
          $("#processing-job-div").hide();
        }
      );
    },

    /**
     *
     * This function check the status of the jobs that generates the initial
     * set of files.
     *
     **/
    checkInitialJobs: function () {
      let vm = this;
      $.get(vm.portal + vm.jobsEndpoint, function(data) {
        $("#processing-job-div").html("");
        $("#processing-job-div").append("<p>Hang tight, we are processing your request: </p>");
        $("#show-hide-network-btn").hide();
        var nonCompletedJobs = 0;
        var successJobs = 0;
        var totalJobs = 0;
        var contents = "";
        var jobErrors = "";
        for(var jobid in data){
          totalJobs += 1;
          contents = contents + "<b> Job: " + jobid + "</b> Status: " + data[jobid]['status'];
          // Only show step if error if they actually have a useful message
          if (data[jobid]['step'] !== null) {
            contents = contents + " Step: " + data[jobid]['step'] + "</br>";
          }
          if (data[jobid]['error']) {
            contents = contents + " Error: " + data[jobid]['error'] + "</br>";
            jobErrors = jobErrors + data[jobid]['error'].replace(/(?:\\n)/g, '<br>') + "</br>";
          }
          // Count the number of jobs that are not completed
          if ((data[jobid]['status'] !== 'error') && (data[jobid]['status'] !== 'success')) {
            nonCompletedJobs += 1;
          } else if (data[jobid]['status'] === 'success') {
            successJobs += 1;
          }
        }

        // If no jobs are in a non completed state, use the callback
        if (totalJobs === 0 || nonCompletedJobs === 0 || totalJobs === successJobs) {
          vm.initialPoll = false;
          // There are no jobs being run
          // To avoid a possible race condition, check if a graph is now available
          $.get(vm.portal + vm.graphEndpoint, function(data) {
            if (data.nodes.length == 0) {
              // No graph is available - execute the callback
              $('#network-header-div').hide();
              if (!vm.isAnalysisPipeline) {
                vm.noInitJobsCallback('processing-job-div', jobErrors);
              } else {
                $("#processing-job-div").html("<h3>Error generating the analysis:</h3><h5>" + jobErrors + '</h5>');
              }
            } else {
              // A graph is available, update the current graph
              vm.updateGraph();
            }
          });
        }
        else {
          vm.initialPoll = true;
          $("#processing-job-div").append(contents);
        }
      })
        .fail(function(object, status, error_msg) {
          $("#processing-job-div").html("Error loading job information: " + status + " " + error_msg);
        }
      );
    }
  },

  /**
   *
   * This function gets called by Vue once the HTML template is ready in the
   * actual DOM. We can use it as an "init" function.
   *
   **/
  mounted() {
    let vm = this;
    vm.new_job_info = null;
    // This initialPoll is used ONLY if the graph doesn't exist yet
    vm.initialPoll = false;
    // This variable is used to show the update countdown on the interface
    // the current wait time is 15 sec
    vm.countdownPoll = 15;
    $('#countdown-span').html(vm.countdownPoll);
    vm.colorScheme = {
      'success': {border: '#00cc00', background: '#7FE57F', highlight: {border: '#00cc00', background: '#a5eda5'}, 'color': '#333333', 'shape': 'ellipse'},
      'running': {border: '#b28500', background: '#ffbf00', highlight: {border: '#b28500', background: '#ffdc73'}, 'color': '#333333', 'shape': 'ellipse'},
      'error': {border: '#ff3333', background: '#ff5b5b', highlight: {border: '#ff3333', background: '#ff8484'}, 'color': '#333333', 'shape': 'ellipse'},
      'in_construction': {border: '#634a00', background: '#e59400', highlight: {border: '#634a00', background: '#efbe66'}, 'color': '#333333', 'shape': 'ellipse'},
      'queued': {border: '#4f5b66', background: '#a7adba', highlight: {border: '#4f5b66', background: '#c0c5ce'}, 'color': '#333333', 'shape': 'ellipse'},
      'waiting': {border: '#4f5b66', background: '#a7adba', highlight: {border: '#4f5b66', background: '#c0c5ce'}, 'color': '#333333', 'shape': 'ellipse'},
      'artifact': {border: '#BBBBBB', background: '#FFFFFF', highlight: {border: '#999999', background: '#FFFFFF'}, 'color': '#333333', 'shape': 'round-triangle'},
      'type': {border: '#BBBBBB', background: '#CCCCCC', highlight: {border: '#999999', background: '#DDDDDD'}, 'color': '#333333', 'shape': 'round-triangle'},
      'deleting': {border: '#ff3333', background: '#ff6347', highlight: {border: '#ff3333', background: '#ff6347'}, 'color': '#333333', 'shape': 'round-triangle'},
      'outdated': {border: '#666666', background: '#666666', highlight: {border: '#000000', background: '#666666'}, 'color': '#ffffff', 'shape': 'round-triangle'},
      'deprecated': {border: '#000000', background: '#000000', highlight: {border: '#000000', background: '#333333'}, 'color': '#ffffff', 'shape': 'vee'}
    };

    show_loading('processing-network-div');
    $("#processing-network-instructions-div").hide();


    $('#run-btn').on('click', function() {
      $('#run-btn').attr('disabled', true);
      this.innerHTML = 'Submitting!';
      vm.runWorkflow();
    });
    $('#run-btn-div').hide();

    $('#refresh-now-link').on('click', function () {
      vm.countdownPoll = 15;
      vm.update_job_status();
    });

    var circle_statuses = [];
    var circle_types = [];
    for (var circle_name in vm.colorScheme) {
      var text = '<td style="padding: 5px; color:' + vm.colorScheme[circle_name]['color'] +
        '; background-color:' + vm.colorScheme[circle_name]['background'] +
        ';"><small>' + circle_name + '</small></td>';
      if (circle_name === 'artifact' || circle_name === 'type' || circle_name === 'deprecated' || circle_name === 'outdated'){
        circle_types.push(text);
      } else {
        circle_statuses.push(text);
      }
    }
    var full_text = '<table style="border-spacing: 3px;border-collapse: separate;">' +
      '<tr>' +
        '<td><small>Job status (circles):</small></td>' +
        '<td>' + circle_statuses.join('') + '</td>' +
        '<td rowspan="2" width="20px">&nbsp;</td>' +
        '<td rowspan="2">&nbsp;&nbsp;&nbsp;</td>' +
        '<td rowspan="2" align="center" id="add-default-workflow">' +
            '<a class="btn btn-success form-control" id="add-default-workflow-btn"><span class="glyphicon glyphicon-flash"></span> Add Default Workflow</a>' +
             "<br/><br/><a href='https://qiita.ucsd.edu/workflows/' target='_blank'> "+
                '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-exclamation-triangle" viewBox="0 0 16 16">' +
                    '<path d="M7.938 2.016A.13.13 0 0 1 8.002 2a.13.13 0 0 1 .063.016.146.146 0 0 1 .054.057l6.857 11.667c.036.06.035.124.002.183a.163.163 0 0 1-.054.06.116.116 0 0 ' +
                        '1-.066.017H1.146a.115.115 0 0 1-.066-.017.163.163 0 0 1-.054-.06.176.176 0 0 1 .002-.183L7.884 2.073a.147.147 0 0 1 .054-.057zm1.044-.45a1.13 1.13 0 0 0-1.96 0L.165 ' +
                        '13.233c-.457.778.091 1.767.98 1.767h13.713c.889 0 1.438-.99.98-1.767L8.982 1.566z"></path>' +
                    '<path d="M7.002 12a1 1 0 1 1 2 0 1 1 0 0 1-2 0zM7.1 5.995a.905.905 0 1 1 1.8 0l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 5.995z"></path>' +
                '</svg>' +
             " Important note about Default Workflow</a>" +
        '</td>' +
      '</tr>' +
      '<tr>' +
        '<td><small>Artifact status (triangles):</small>' +
        '<td>' + circle_types.join('') + '</td>' +
      '</tr>' +
    '</table>';
    $('#circle-explanation').html(full_text);

    $('#add-default-workflow-btn').on('click', function () {
      $('#add-default-workflow').attr('disabled', true);
      document.getElementById('add-default-workflow-btn').innerHTML = 'Submitting!';
      $.post(vm.portal + '/study/process/workflow/default/', {prep_id: vm.elementId}, function(data) {
        if (data['msg_error'] !== null){
          $('#add-default-workflow-btn').attr('disabled', false);
          bootstrapAlert('Error generating workflow: ' + data['msg_error'].replace("\n", "<br/>"));
        } else {
          vm.updateGraph();
        }
      });
      document.getElementById('add-default-workflow-btn').innerHTML = ' Add Default Workflow';
    });

    // This call to udpate graph will take care of updating the jobs
    // if the graph is not available
    vm.updateGraph();
    vm.interval = setInterval(function() {
      vm.countdownPoll -= 1;
      $('#countdown-span').html(vm.countdownPoll);
      if (vm.countdownPoll === 0) {
        // Reset the counter for every 15 seconds
        vm.countdownPoll = 15;

        // Check for the initial poll - it only happens if a graph doesn't exist yet
        if (vm.initialPoll) {
          vm.updateGraph();
        }

        // Update the status of the jobs
        vm.update_job_status();
      }
    }, 1000);
  }
});


/**
 *
 * Creates a new Vue object for the Processing Network in a safe way
 *
 *
 **/
function newProcessingNetworkVue(target) {
  if (processingNetwork !== null) {
    processingNetwork.$refs.procGraph.destroy();
  }
  processingNetwork = new Vue({el: target});
}
