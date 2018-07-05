var sampleTemplatePage = null;

// taken from https://stackoverflow.com/a/19963011
function unique(array) {
    return $.grep(array, function(el, index) {
        return index == $.inArray(el, array);
    });
}

function get_column_summary(study_id, portal, column, numSamples){
  var row = $('.' + column + 'collapsed');

  if (row.is(":hidden")) {
    var cell = $(row.children()[0]);
    cell.html('<img src="' + portal + '/static/img/waiting.gif" style="display:block;margin-left: auto;margin-right: auto"/>');
    $.get(portal + '/study/description/sample_template/columns/', {study_id: study_id, column: column}, function(data) {
      cell.html('');
      var values = data['values'];
      var uniques = unique(values);
      var table = $('<table>').addClass('table').appendTo(cell);
      if (uniques.length === 1) {
        var tr = $('<tr>').appendTo(table);
        var td = $('<td>').append(uniques[0] + ' is repeated in all rows.').appendTo(tr);
      } else if (uniques.length === numSamples) {
        var tr = $('<tr>').appendTo(table);
        var td = $('<td>').append('All the values in this category are different').appendTo(tr);
      } else {
        var counts = {};
        for (let u of uniques) { counts[u] = 0; }
        for (let v of values) { counts[v]++; }
        for (let u of uniques) {
          var tr = $('<tr>').appendTo(table);
          var td = $('<td>').append(u).appendTo(tr);
          var td = $('<td>').append(counts[u]).appendTo(tr);
        }
      }
    })
  }
}

Vue.component('sample-template-page', {
  template: '<div id="sample-template-main-div">' +
              // Title div
              '<div class="row">' +
                '<div class="col-md-12">' +
                  '<h3>Sample Information<span id="title-h3"></span></h3>' +
                '</div>' +
              '</div>' +
              // Processing div
              '<div class="row" id="st-processsing-div" style="border-radius: 10px; background: #EEE;">' +
                '<div class="col-md-12">' +
                  '<h4>We are processing your request via job "<span id="job-id-span"></span>". Status: "<span id="job-status-span"></span>"</h4>' +
                '</div>' +
              '</div>' +
              '</br>' +
              // Content div
              '<div class="row">' +
                '<div class="col-md-12" id="sample-template-contents">' +
                '</div>' +
              '</div>' +
            '</div>',
  props: ['portal', 'study-id'],
  methods: {
    /**
     *
     * Checks the status of the job performing some task over the sample
     * information
     *
     **/
    checkJob: function() {
      let vm = this;
      $.get(vm.portal + '/study/process/job/', {job_id: vm.job}, function(data) {
        var jobStatus;
        jobStatus = data['job_status'];
        $('#job-id-span').text(data['job_id']);
        $('#job-status-span').text(jobStatus);

        if (jobStatus === 'error' || jobStatus === 'success') {
          vm.stopJobCheckInterval();
          // Hide the processing div
          $('#st-processsing-div').hide();
          // Enable interaction bits
          $('#update-btn-div').show();
          $('.st-interactive').prop('disabled', false);
          if (jobStatus === 'error') {
            // The job errored - show the error
            bootstrapAlert(data['job_error'], "danger");
          } else {
            // The job succeeded - reload the interface to show changes
            if (vm.refresh) {
              vm.refresh = false;
              location.reload();
            } else {
              vm.updateSampleTemplateOverview();
            }
          }
        }
      })
        .fail(function(object, status, error_msg) {
          bootstrapAlert("Error checking the job status: " + object.statusText, "danger");
        });
    },

    /**
     *
     * Starts the interval that checks the status of the job.
     *
     **/
    startJobCheckInterval: function(jobId) {
      let vm = this;
      vm.job = jobId;

      // Hide the current error message (if any)
      $('#alert-message').alert('close');
      // Show the processing div
      $('#st-processsing-div').show();
      // Disable interaction bits
      $('.st-interactive').prop('disabled', true);
      $('#update-btn-div').hide();
      // Force the first check to happen now
      vm.checkJob();
      // Set the interval for further checking - this jobs tend to be way faster
      // hence setting the interval every 2 seconds.
      vm.interval = setInterval(vm.checkJob, 2000);
    },

    /**
     *
     * Stops the interval checking the status of the job
     *
     **/
    stopJobCheckInterval: function() {
      let vm = this;
      clearInterval(vm.interval);
    },

    /**
     *
     * Performs a call to the server API to create a new sample template
     *
     **/
    createSampleTemplate: function() {
      let vm = this;
      var fp = $('#file-select').val();
      var dtype = $('#data-type-select').val();
      vm.refresh = true;

      $.post(vm.portal + '/study/description/sample_template/', {study_id: vm.studyId, filepath: fp, data_type: dtype}, function(data) {
          vm.startJobCheckInterval(data['job']);
      })
        .fail(function(object, status, error_msg) {
          bootstrapAlert("Error creating sample information: " + object.statusText, "danger");
        });
    },

    /**
     *
     * Performs a call to the server API to udpate the sample information
     *
     **/
    updateSampleTemplate: function() {
      let vm = this;
      $.ajax({
        url: vm.portal + '/study/description/sample_template/',
        type: 'PATCH',
        data: {'op': 'replace', 'path': vm.studyId + '/data/', 'value': $('#file-select').val()},
        success: function(data) {
          vm.startJobCheckInterval(data['job']);
        },
        error: function (object, status, error_msg) {
          bootstrapAlert("Error updating sample template: " + error_msg, "danger")
        }
      });
    },

    /**
     *
     * Performs a call to the server API to delete a column from the sample template
     *
     * @param category str The category to be removed
     * @param rowId int The row number where this category was placed
     *
     **/
    deleteColumn: function(category, rowId) {
      let vm = this;
      $.ajax({
        url: vm.portal + '/study/description/sample_template/',
        type: 'PATCH',
        data: {'op': 'remove', 'path': vm.studyId + '/columns/' + category},
        success: function(data) {
          vm.rowId = rowId;
          vm.rowType = 'column';
          vm.startJobCheckInterval(data['job']);
        },
        error: function (object, status, error_msg) {
          bootstrapAlert("Error deleting column: " + error_msg, "danger")
        }
      });
    },

    /**
     *
     * Performs a call to the server API to delete a sample from the sample template
     *
     * @param sample str The sample to be removed
     * @param rowId int The row number where this sample was placed
     *
     **/
    deleteSample: function(sample, rowId) {
      let vm = this;
      $.ajax({
        url: vm.portal + '/study/description/sample_template/',
        type: 'PATCH',
        data: {'op': 'remove', 'path': vm.studyId + '/samples/' + sample},
        success: function(data) {
          vm.rowId = rowId;
          vm.rowType = 'sample';
          vm.startJobCheckInterval(data['job']);
        },
        error: function (object, status, error_msg) {
          bootstrapAlert("Error deleting sample: " + error_msg, "danger")
        }
      });
    },

    /**
     *
     * Performs a call to the server API to delete the sample template
     *
     **/
    deleteSampleTemplate: function() {
      let vm = this;
      if(confirm("Are you sure you want to delete the sample information?")) {
        vm.refresh = true;
        $.ajax({
          url: vm.portal + '/study/description/sample_template/?study_id=' + vm.studyId,
          type: 'DELETE',
          success: function(data) {
            vm.startJobCheckInterval(data['job']);
          },
          error: function (object, status, error_msg) {
            bootstrapAlert("Error deleting sample information: " + error_msg, "danger")
          }
        });
      }
    },

    /**
     *
     * Creates the GUI for the summary table
     *
     **/
    populateSampleInfoTable: function() {
      let vm = this;
      // Gathering this information is expensive in some studies. By issuing
      // a different AJAX call for it, we can keep showing the rest of the interface
      // (and interact with it) without having to wait for this information to
      // show up - also the creation of the table occurs now in client side
      // rather than in server side.
      $.get(vm.portal + '/study/description/sample_template/columns/', {study_id: vm.studyId}, function(data) {
        var catValues, $tr, $td, rowIdx, collapsedId, $trVal, $div, $btn;
        $div = $('<div>').addClass('panel panel-default').appendTo('#sample-info-tab');
        $('<div>').addClass('panel-heading').appendTo($div).append('Information summary');
        var $table = $('<table>').addClass('table').appendTo($div);
        var categories = data['values'];
        categories.sort(function(a, b){return a[0].localeCompare(b[0], 'en', {'sensitivity': 'base'});});

        rowIdx = 0;
        for (var cat of categories) {
          $tr = $('<tr>').attr('id', 'col-row-' + rowIdx).appendTo($table);
          if (vm.editable && vm.userCanEdit) {
            $td = $('<td>').appendTo($tr);
            $btn = $('<button>').addClass('btn btn-danger st-interactive').appendTo($td).attr('data-column', cat).attr('data-row-id', rowIdx);
            $('<span>').addClass('glyphicon glyphicon-trash').appendTo($btn);
            $btn.on('click', function () {
              if (confirm('Are you sure you want to delete `' + $(this).attr('data-column') + '`?')) {
                vm.deleteColumn($(this).attr('data-column'), $(this).attr('data-row-id'));
              }
            });
          }
          rowIdx += 1;
          $td = $('<td>').appendTo($tr);
          $('<b>').append(cat + ': ').appendTo($td);
          $td.append('&nbsp;&nbsp;&nbsp;&nbsp;');
          collapsedId = cat + 'collapsed';
          fcall = 'get_column_summary(' + vm.studyId + ', "' + vm.portal + '", "' + cat + '", ' + vm.numSamples + ')';
          $bt = $('<button>').addClass('btn btn-default').attr('onclick', fcall).attr('data-toggle', 'collapse').attr('data-target', '.' + collapsedId).append('Values').appendTo($td);
          $trVal = $('<tr>').addClass('collapse').addClass(collapsedId).appendTo($table);
          $('<td>').attr('colspan', '3').append('&nbsp;').appendTo($trVal);
        }

        // Scroll to the desired row
        if(vm.rowType === 'column' && vm.rowId !== null) {
          // taken from: http://stackoverflow.com/a/2906009
          var container = $('html, body');
          var scrollTo = $('#col-row-' + vm.rowId);
          container.animate({
              scrollTop: scrollTo.offset().top - container.offset().top + container.scrollTop()
          });
          vm.rowId = null;
        }
      })
        .fail(function(object, status, error_msg) {
          bootstrapAlert("Error loading sample information: " + object.statusText, "danger");
        });
    },

    /**
     *
     * Creates the GUI for the Sample-Prep table
     *
     **/
    populateSamplePrepTab: function() {
      let vm = this;
      show_loading('sample-prep-tab');
      $.get(vm.portal + '/study/description/sample_summary/', {study_id: vm.studyId}, function(data) {
        $('#sample-prep-tab').html(data);
      })
        .fail(function(object, status, error_msg) {
          bootstrapAlert("Error loading sample-prep information: " + object.statusText, "danger");
        });
    },

    /**
     *
     * Creates the GUI for the case that a sample template exists
     *
     **/
    populateExistingSampleTemplate: function() {
      let vm = this;
      var $btn, $div, $small, $row, $col, $ul, $li, $tab;

      //  Clear the contents of the div
      $('#sample-template-contents').empty();

      // Add the buttons next to the title
      // Download Sample Information button
      $('#title-h3').append(' ');
      $btn = $('<a>').addClass('btn btn-default').attr('href', vm.portal + '/download/' + vm.downloadId).appendTo('#title-h3');
      $('<span>').addClass('glyphicon glyphicon-download-alt').appendTo($btn);
      $btn.append(' Sample Info');
      // Delete button (only if the user can edit)
      if (vm.userCanEdit) {
        $('#title-h3').append(' ');
        $btn = $('<button>').addClass('btn btn-danger st-interactive').on('click', vm.deleteSampleTemplate).appendTo('#title-h3');
        $('<span>').addClass('glyphicon glyphicon-trash').appendTo($btn);
        $btn.append(' Delete');
      }
      // Show older files button (only if the sample information has older files)
      if (vm.oldFiles.length > 0) {
        // Add the button
        $('#title-h3').append(' ');
        $btn = $('<button>').addClass('btn btn-default').attr('data-toggle', 'collapse').attr('data-target', '#st-old-files').appendTo('#title-h3');
        $('<span>').addClass('glyphicon glyphicon-eye-open').appendTo($btn);
        $btn.append(' Show old files');

        // Add the div that hold the old files
        $div = $('<div>').attr('id', 'st-old-files').addClass('collapse').appendTo('#sample-template-contents');
        $div.css('padding', '10px 10px 10px 10px').css('border-radius', '10px').css('background', '#EEE');
        $small = $('<small>').appendTo($div).append('<label>Old files</label>');
        for (var oldFile of vm.oldFiles) {
          $small.append('<br/>' + oldFile);
        }
      }

      // After adding the buttons we can add the two tabs - one holding the Sample Information
      // and the other one holding the Sample and preparation summary
      $row = $('<div>').addClass('row').appendTo('#sample-template-contents');
      $col = $('<div>').addClass('col-md-12').appendTo($row);

      // The two "pills"
      $ul = $('<ul>').addClass('nav nav-pills').appendTo($col);
      $li = $('<li>').css('border', '1px solid #428bca').css('border-radius', '5px').appendTo($ul);
      if (vm.rowType == 'column') {
        $li.addClass('active');
      }
      $('<a>').attr('data-toggle', 'tab').attr('href', '#sample-info-tab').appendTo($li).append('Sample Information');
      $li = $('<li>').css('border', '1px solid #428bca').css('border-radius', '5px').appendTo($ul);
      if (vm.rowType == 'sample') {
        $li.addClass('active');
      }
      $('<a>').attr('data-toggle', 'tab').attr('href', '#sample-prep-tab').appendTo($li).append('Sample-Prep Summary');

      // The two tab divs are contained in a single tab-content div
      $div = $('<div>').addClass('tab-content').appendTo($col);
      $tab = $('<div>').addClass('tab-pane').attr('id', 'sample-info-tab').appendTo($div);
      if (vm.rowType == 'column') {
        $tab.addClass('active');
      }
      // Add the number of samples
      $tab.append('<label>Number of samples:</label> ' + vm.numSamples + '</br>')
      // Add the number of columns
      $tab.append('<label>Number of columns:</label> ' + vm.numColumns + '</br>')
      // Add the select to update the sample information
      if (vm.userCanEdit) {
        $row = $('<div>').attr('id', 'update-st-div').addClass('row form-group').appendTo($tab);
        $('<label>').addClass('col-sm-2 col-form-label').append('Update sample information:').appendTo($row);
        $col = $('<div>').addClass('col-sm-3').appendTo($row);
        $select = $('<select>').attr('id', 'file-select').addClass('form-control').appendTo($col);
        $('<option>').attr('value', "").append('Choose file...').appendTo($select);
        for (var opt of vm.uploadedFiles) {
          $('<option>').attr('value', opt).append(opt).appendTo($select);
        }
        // Add the button to trigger the update
        $col = $('<div>').addClass('col-sm-1').attr('id', 'update-btn-div').appendTo($row).hide();
        $('<button>').addClass('btn btn-success form-control').append('Update').appendTo($col).on('click', vm.updateSampleTemplate);
        $('#file-select').on('change', function() {
          if (this.value === "") {
            $('#update-btn-div').hide()
          } else {
            $('#update-btn-div').show()
          }
        });
      }

      // Populate the sample information table
      vm.populateSampleInfoTable();

      // Sample-prep tab
      $tab = $('<div>').addClass('tab-pane').attr('id', 'sample-prep-tab').appendTo($div);
      if (vm.rowType === 'sample') {
        $tab.addClass('active');
      }
      vm.populateSamplePrepTab();
    },

    /**
     *
     * Creates the GUI to create a new sample template
     *
     **/
    populateNewSampleTemplateForm: function() {
      let vm = this;
      var $row, $col, $select;

      // Clear the contents of the div
      $('#sample-template-contents').empty();

      // To avoid code duplication creating the DOM elements, create a list
      // with the contents and create the DOM elements in the for loop
      var rowContents = [
        // First one contains the uploaded files
        {label: 'Select sample information file:', selectId: 'file-select', options: vm.uploadedFiles, placeholder: 'Choose file...'},
        // Second one contains the data types
        {label: 'If uploading a QIIME mapping file, select the data type of the prep information:', selectId: 'data-type-select', options: vm.dataTypes, placeholder: 'Choose a data type...'}]

      // Create the DOM elements
      for (var rC of rowContents) {
        $row = $('<div>').addClass('row form-group').appendTo('#sample-template-contents');
        $('<label>').addClass('col-sm-3 col-form-label').append(rC.label).appendTo($row);
        $col = $('<div>').addClass('col-sm-3').appendTo($row);
        $select = $('<select>').attr('id', rC.selectId).addClass('form-control').appendTo($col);
        $('<option>').attr('value', "").append(rC.placeholder).appendTo($select);
        for (var opt of rC.options) {
          $('<option>').attr('value', opt).append(opt).appendTo($select);
        }
      }

      // Add the button - by default hidden
      $row = $('<div>').attr('id', 'create-btn-div').addClass('row form-group').appendTo('#sample-template-contents').hide();
      $col = $('<div>').addClass('col-sm-1').appendTo($row);
      $('<button>').addClass('btn btn-success form-control st-interactive').append('Create').appendTo($col).on('click', vm.createSampleTemplate);

      // Show/hide the button base on the value of the file selector
      $('#file-select').on('change', function() {
        if (this.value === "") {
          $('#create-btn-div').hide()
        } else {
          $('#create-btn-div').show()
        }
      });
    },

    /**
     *
     * Performs a query to the server to update the sample template overview information
     *
     **/
    updateSampleTemplateOverview: function () {
      let vm = this;

      $.get(vm.portal + '/study/description/sample_template/overview/', {study_id: vm.studyId}, function(data) {
        vm.exists = data['exists'];
        vm.dataTypes = data['data_types'];
        vm.uploadedFiles = data['uploaded_files'];
        vm.userCanEdit = data['user_can_edit'];
        vm.job = data['job'];
        vm.downloadId = data['download_id'];
        vm.oldFiles = data['old_files'];
        vm.numSamples = data['num_samples'];
        vm.numColumns = data['num_columns'];

        // Populate the sample-template-contents
        $('#title-h3').empty();
        if (!vm.exists) {
          vm.populateNewSampleTemplateForm();
        } else {
          vm.populateExistingSampleTemplate();
        }

        // Check the job for first time
        if (vm.job !== null) {
          $.get(vm.portal + '/study/process/job/', {job_id: vm.job}, function(data) {
            var jobStatus = data['job_status'];
            if (jobStatus === 'error') {
              bootstrapAlert(data['job_error'], "danger");
            } else if (jobStatus !== 'success') {
              vm.startJobCheckInterval(vm.job);
            }
          })
            .fail(function(object, status, error_msg) {
              bootstrapAlert("Error checking the job status: " + object.statusText, "danger");
            });
        }

      })
        .fail(function(object, status, error_msg) {
          bootstrapAlert("Error gathering Sample Information from server: " + object.statusText, "danger");
        });
    },

    /**
     *
     * Cleans up the current object
     *
     **/
    destroy: function() {
      let vm = this;
      vm.stopJobCheckInterval()
    }
  },
  /**
   *
   * This function gets called by Vue once the HTML template is ready in the DOM
   *
   **/
  mounted() {
    let vm = this;

    vm.interval = null;
    vm.job = null;
    vm.editable = true;
    vm.rowId = null;
    vm.rowType = 'column';
    vm.refresh = false;
    $('#st-processsing-div').hide();

    show_loading('sample-template-contents');

    // Get the overview information from the server
    vm.updateSampleTemplateOverview();
  }
});

/**
 *
 * Creates a new Vue object for the Sample Template in a safe way
 *
 * @param target str The id of the target div for the new Vue object
 *
 **/
function newSampleTemplateVue(target) {
  if (sampleTemplatePage !== null) {
    sampleTemplatePage.$refs.stElem.destroy();
  }
  sampleTemplatePage = new Vue({el: target});
};
