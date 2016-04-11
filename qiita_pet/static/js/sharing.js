function init_sharing(portal) {
  $('#shares-select').select2({
    ajax: {
      url: portal + "/study/sharing/autocomplete/",
      dataType: 'json',
      delay: 250,
      data: function (params) {
        return {text: params.term};
      },
      cache: true
    },
    minimumInputLength: 1,
    formatResult: function (data, term) {
      return data;
    }
  });

  $('#shares-select').on("select2:select", function (e) {
    console.log(e);
    update_share($('#shares-select').attr('data-share-url'), {selected: e.params.data.text});
  });

  $('#shares-select').on("select2:unselect", function (e) {
    update_share($('#shares-select').attr('data-share-url'), {deselected: e.params.data.text});
  });
}

function modify_sharing(url, id) {
  var shared_list;
  $('#shares-select').attr('data-current-id', id);
  $.get(url, {id: id})
    .done(function(data) {
      var users_links = JSON.parse(data);
      var users = users_links.users;
      //empty dropdown and repopulate with new study shared values
      $('#shares-select').html('');
      for(var i=0;i<users.length;i++) {
        var shared = new Option(users[i], users[i], true, true);
        $("#shares-select").append(shared).trigger('change');
      }
      $("#shares-select").trigger("change");
    });
}

function update_share(url, params) {
  share_id = $('#shares-select').attr('data-current-id');
  data = params || {};
  data.id = share_id;
  $.get(url, data)
    .done(function(data) {
      users_links = JSON.parse(data);
      links = users_links.links;
      $("#shared_html_"+share_id).html(links);
    });
}