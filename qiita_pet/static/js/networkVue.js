// This global variable holds the Vue object - it is needed to be able to
// trigger some functions from other elements
var processingNetwork = null;

/**
 *
 * Toggle the graph view
 *
 * Show/hide the graph div and update GUI accordingly
 *
 **/
function toggleNetworkGraph() {
  if($("#processing-network-div").css('display') == 'none' ) {
    $("#processing-network-div").show();
    $("#show-hide-network-btn").text("Hide");
  } else {
    $("#processing-network-div").hide();
    $("#show-hide-network-btn").text("Show");
  }
};

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
                  // Graph navigation toggler
                  '<div class="row">' +
                    '<div class="col-md-2">' +
                      '<h4>Graph navigation</h4>' +
                    '</div>' +
                    '<div class="col-md-1">' +
                      '<input type="checkbox" id="interaction-btn" data-toggle="toggle">' +
                    '</div>' +
                  '</div>' +
                  // Run workflow button
                  '<div class="row" id="run-btn-div">' +
                    '<div class="col-md-2">' +
                      '<h4><span class="blinking-message">Start workflow:</h4></span>' +
                    '</div>' +
                    '<div class="col-md-1">' +
                      '<a class="btn btn-success form-control" id="run-btn"><span class="glyphicon glyphicon-play"></span> Run</a>' +
                    '</div>' +
                  '</div>' +
                  '<div class="row">' +
                    '<div class="col-md-12">' +
                      '<b>Click circles for more information - This graph will refresh in <span id="countdown-span"></span> seconds or reload <a href="#" id="refresh-now-link">now</a></b>' +
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
                '<div class="col-md-12" style="width:90%" id="processing-results">' +
                '</div>' +
              '</div>' +
            '</div>',
  props: ['portal', 'graph-endpoint', 'jobs-endpoint', 'no-init-jobs-callback', 'is-analysis-pipeline'],
  methods: {
    /**
     *
     * Enables the graph interaction
     *
     **/
    enableGraphInteraction: function () {
      let vm = this;
      options = {interaction: { dragNodes: false,
                                    dragView: true,
                                    zoomView: true,
                                    selectConnectedEdges: true,
                                    navigationButtons: true,
                                    keyboard: false}};
      vm.network.setOptions(options);
    },

    /**
     *
     * Disables the graph interaction
     *
     **/
    disableGraphInteraction: function() {
      let vm = this;
      options = {interaction: { dragNodes: false,
                                dragView: false,
                                zoomView: false,
                                selectConnectedEdges: false,
                                navigationButtons: false,
                                keyboard: false}};
      vm.network.setOptions(options);
    },

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
     * Enables/Disables the interaction with the graph
     *
     **/
    toggleGraphInteraction: function () {
      let vm = this;
      var options;
      if ($('#interaction-btn').prop('checked')) {
        vm.enableGraphInteraction();
      } else {
        vm.disableGraphInteraction();
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
            jobNode = vm.nodes_ds.get(jobId);

            // If the job is in one of the "running" states, we add it to the runningJobs list
            if (jobStatus === 'running' || jobStatus === 'queued' || jobStatus === 'waiting') {
              vm.runningJobs.push(jobId);
            }

            if (jobNode['status'] !== jobStatus) {
              // The status of the job changed.
              // we decide what to do based on the new status.
              if (jobStatus === 'success' || jobStatus === 'error') {
                // If the job succeeded or failed, we need to reset the entire graph
                // because the changes on the nodes are substantial
                needsUpdate = true;
              } else {
                // In this case the job changed to either 'running', 'queued' or 'waiting'. In
                // this case, we just need to update the internal values of the nodes and the colors
                jobNode.color = vm.colorScheme[jobStatus];
                jobNode.status = jobStatus;
                vm.nodes_ds.update(jobNode);
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
      var queue = [jobId];
      var edge_list = vm.edges_ds.get();
      var current;
      var edge;
      var currentNode;
      while(queue.length !== 0) {
        current = queue.pop();

        // Add all children nodes to the queue, and remove the edges
        // connecting the current node to its children
        for(var i in edge_list) {
          edge = edge_list[i];
          if(edge.from == current) {
            if($.inArray(edge.to, queue) == -1) {
              queue.push(edge.to);
            }
            vm.edges_ds.remove(edge.id);
          }
        }

        currentNode = vm.nodes_ds.get(current);
        if(currentNode.group === 'job') {
          if(currentNode.status === 'in_construction') {
            vm.inConstructionJobs -= 1;
          }
        }
        vm.nodes_ds.remove(current);
      }
      var edges_to_remove = vm.edges_ds.get(
        {filter: function(item) {
          return item.to == jobId;
        }});
      var edge_ids = [];
      $(edges_to_remove).each(function(i){
        edge_ids.push(edges_to_remove[i].id);
      });

      vm.edges_ds.remove(edge_ids);
      vm.network.redraw();

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
      let vm = this;
      $.post(vm.portal + "/study/process/workflow/run/", {workflow_id: vm.workflowId}, function(data){
        bootstrapAlert("Workflow " + vm.workflowId + " submitted", "success");
        $('#run-btn-div').hide();
        $("#processing-results").empty();
        vm.updateGraph();
      })
        .fail(function(object, status, error_msg) {
          bootstrapAlert("Error submitting workflow: " + object.statusText, "danger");
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
        var h = $("<h3>").text('Job ' + data['job_id'] + ' ').appendTo("#processing-results");

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
        if (data['job_step'] !== null) {
          rowsContent.push(['Current step:', data['job_step']]);
        }

        if (data['job_status'] === 'error' && data['job_error'] !== null) {
          rowsContent.push(['Error message:', data['job_error']]);
        }

        // Create the DOM elements to add the rows content
        for (var row of rowsContent) {
          $rowDiv = $('<div>').addClass('row').addClass('form-group').appendTo("#processing-results");
          $('<label>').addClass('col-sm-1 col-form-label').text(row[0]).appendTo($rowDiv);
          $colDiv = $('<div>').addClass('col-sm-5').appendTo($rowDiv).html(row[1]);
        }

        $("#processing-results").append($("<h4>").text('Job parameters:'));

        for(var key in data.job_parameters){
          $rowDiv = $('<div>').addClass('row').addClass('form-group').appendTo("#processing-results");
          $('<label>').addClass('col-sm-2 col-form-label').text(key + ':').appendTo($rowDiv);
          $colDiv = $('<div>').addClass('col-sm-5').appendTo($rowDiv).html(data.job_parameters[key]);
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
        if (p_type == 'integer') {
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
          $inp.prop('checked', dflt_val);
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
      $.get(vm.portal + '/study/process/commands/options/', {command_id: cmd_id})
        .done(function(data){
            // Put first the required parameters
            $("#cmd-opts-div").append($('<h4>').text('Required parameters:'));
            var keys = Object.keys(data.req_options).sort(function(a, b){return a.localeCompare(b, 'en', {'sensitivity': 'base'});});
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
     * @param p_nodes list The ids of the selected artifacts
     *
     * This function executes an AJAX call to retrieve all the commands that can
     * process the selected artifacts. It generates the interface so the user
     * can select which command should be added to the workflow
     *
     **/
    loadArtifactType: function(p_nodes) {
      let vm = this;
      var types = [];
      var sel_artifacts_info = {};
      var node;
      var target = $("#processing-results");

      for(var i=0; i < p_nodes.length; i++) {
        node = vm.nodes_ds.get(p_nodes[i]);
        if(types.indexOf(node.type) === -1) {
          types.push(node.type);
        }
        sel_artifacts_info[node.id] = {'type': node.type, 'name': node.label}
      }
      $.get(vm.portal + '/study/process/commands/', {artifact_types: types, include_analysis: vm.isAnalysisPipeline})
        .done(function (data) {
          target.empty();

          // Create the command select dropdown
          var $rowDiv = $('<div>').addClass('row').addClass('form-group').appendTo(target);
          $('<label>').addClass('col-sm-2').addClass('col-form-label').text('Choose command:').appendTo($rowDiv).attr('for', 'command-sel');
          var $colDiv = $('<div>').addClass('col-sm-3').appendTo($rowDiv);
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
      // Fun fact - although it seems counterintuitive, in vis.Network we
      // first need to add the edge and then we can add the node. It doesn't
      // make sense, but it is how it works
      $(job_info.inputs).each(function(){
        vm.edges_ds.add({id: vm.edges_ds.length + 1, from: this, to: job_info.id});
      });
      vm.nodes_ds.add({id: job_info.id, group: "job", label: job_info.label, color: vm.colorScheme.in_construction, status: 'in_construction'});
      $(job_info.outputs).each(function(){
        var out_name = this[0];
        var out_type = this[1];
        var n_id = job_info.id + ":" + out_name;
        vm.edges_ds.add({id: vm.edges_ds.length + 1, from: job_info.id, to: n_id });
        vm.nodes_ds.add({id: n_id, label: out_name + "\n(" + out_type + ")", group: "type", name: out_name, type: out_type});
      });
      vm.network.redraw();
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

      vm.nodes_ds = new vis.DataSet(vm.nodes);
      vm.edges_ds = new vis.DataSet(vm.edges);
      var data = {
        nodes: vm.nodes_ds,
        edges: vm.edges_ds
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
          dragView: false,
          zoomView: false,
          selectConnectedEdges: false,
          navigationButtons: false,
          keyboard: false
        },
        groups: {
          jobs: {
            color: '#FF9152'
          },
          artifact: {
            color: '#FFFFFF'
          },
          type: {
            color: '#BBBBBB'
          }
        }
      };

      vm.network = new vis.Network(container, data, options);
      vm.network.on("click", function (properties) {
        var ids = properties.nodes;
        if (ids.length == 0) {
          return
        }
        // [0] cause users can only select 1 node
        var clickedNode = vm.nodes_ds.get(ids)[0];
        var element_id = ids[0];
        if (clickedNode.group == 'artifact') {
          vm.populateContentArtifact(element_id, target_details);
        } else {
          var ei = element_id.split(':');
          if (ei.length == 2) {
            vm.loadArtifactType([element_id], false, target_details);
          } else {
            vm.populateContentJob(element_id, target_details);
          }
        }
      });

      // Make sure that the button and the behavior matches
      if ($('#interaction-btn').prop('checked')) {
        vm.enableGraphInteraction();
      } else {
        vm.disableGraphInteraction();
      }
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
            vm.edges.push({from: data.edges[i][0], to: data.edges[i][1], arrows:'to'});
          }
          // Format node list data
          for(var i = 0; i < data.nodes.length; i++) {
            vm.nodes.push({id: data.nodes[i][2], label: data.nodes[i][3], type: data.nodes[i][1], group: data.nodes[i][0], color: vm.colorScheme[data.nodes[i][4]], status: data.nodes[i][4]});
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
          $("#processing-job-div").hide();
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
        var nonCompletedJobs = 0;
        var successJobs = 0;
        var totalJobs = 0;
        var contents = "";
        var jobErrors = "";
        for(var jobid in data){
          totalJobs += 1;
          contents = contents + "<b> Job: " + jobid + "</b> Status: " + data[jobid]['status'];
          // Only show step if error if they actually have a useful message
          if (data[jobid]['step']) {
            contents = contents + " Step: " + data[jobid]['step'] + "</br>";
          }
          if (data[jobid]['error']) {
            contents = contents + " Error: " + data[jobid]['error'] + "</br>";
            jobErrors = jobErrors + data[jobid]['error'] + "</br>";
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
              vm.noInitJobsCallback('processing-job-div', jobErrors);
            } else {
              // A graph is available, update de current graph
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
    // This initialPoll is used ONLY if the graph doesn't exist yet
    vm.initialPoll = false;
    // This variable is used to show the update countdown on the interface
    // the current wait time is 15 sec
    vm.countdownPoll = 15;
    $('#countdown-span').html(vm.countdownPoll);
    vm.colorScheme = {
      'success': {border: '#00cc00', background: '#7FE57F', highlight: {border: '#00cc00', background: '#a5eda5'}},
      'running': {border: '#b28500', background: '#ffbf00', highlight: {border: '#b28500', background: '#ffdc73'}},
      'error': {border: '#ff3333', background: '#ff5b5b', highlight: {border: '#ff3333', background: '#ff8484'}},
      'in_construction': {border: '#634a00', background: '#e59400', highlight: {border: '#634a00', background: '#efbe66'}},
      'queued': {border: '#4f5b66', background: '#a7adba', highlight: {border: '#4f5b66', background: '#c0c5ce'}},
      'waiting': {border: '#4f5b66', background: '#a7adba', highlight: {border: '#4f5b66', background: '#c0c5ce'}},
      'artifact': {border: '#BBBBBB', background: '#FFFFFF', highlight: {border: '#999999', background: '#FFFFFF'}},
      'type': {border: '#BBBBBB', background: '#CCCCCC', highlight: {border: '#999999', background: '#DDDDDD'}}};
    show_loading('processing-network-div');
    $("#processing-network-div").hide();

    $('#run-btn').on('click', function() { vm.runWorkflow(); });
    $('#run-btn-div').hide();

    $('#interaction-btn').bootstrapToggle({
      on: 'Enabled',
      off: 'Disabled',
      onstyle: 'success',
      offstyle: 'danger'}
    );

    $('#interaction-btn').change(vm.toggleGraphInteraction);

    $('#refresh-now-link').on('click', function () {
      vm.countdownPoll = 15;
      vm.update_job_status();
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
