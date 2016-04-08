var current_study = null;

$(document).ready(function () {
  $('#shares-select').select2({
    ajax: {
      url: "/study/sharing/autocomplete/",
      dataType: 'json',
      delay: 250,
      data: function (params) {
        return {text: params.term};
      },
      cache: true
    },
    minimumInputLength: 1,
    formatResult: function (data, term) {
      console.log(data);
      return data;
    }
  });

  $('#shares-select').on("select2:select", function (e) {
    $.get('/study/sharing/', {study_id: current_study, selected: e.params.data.text})
      .done(function(data) {
        users_links = JSON.parse(data);
        links = users_links['links'];
        document.getElementById("shared_html_"+current_study).innerHTML = links;
      });
  });

  $('#shares-select').on("select2:unselect", function (e) {
    $.get('/study/sharing/', {study_id: current_study, deselected: e.params.data.text})
      .done(function(data) {
        users_links = JSON.parse(data);
        links = users_links['links'];
        document.getElementById("shared_html_"+current_study).innerHTML = links;
      });
  });
});

function modify_sharing(study_id) {
var shared_list;
current_study = study_id;
$.get('/study/sharing/', {study_id: study_id})
    .done(function(data) {
      users_links = JSON.parse(data);
      users = users_links.users;
      //empty dropdown and repopulate with new study shared values
      $('#shares-select').html('');
      for(i=0;i<users.length;i++) {
        var shared = new Option(users[i], users[i], true, true);
        $("#shares-select").append(shared).trigger('change');
      }
      $("#shares-select").trigger("change");
    });
}