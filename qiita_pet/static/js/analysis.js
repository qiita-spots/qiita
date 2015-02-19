function displaySelected() {
  var linktext = document.getElementById("shselected");
  var seldiv = document.getElementById("selected");
  var sampdiv = document.getElementById("availstudies");
  var buttondiv = document.getElementById("seperator");
  if(seldiv.style.display == "none") {
    sampdiv.style.bottom = "30%";
    sampdiv.style.height='60%';
    buttondiv.style.bottom = "25%";
    seldiv.style.height = "25%";
    seldiv.style.display = "";
    linktext.innerHTML = "Hide selected samples";
  }
  else {
    sampdiv.style.bottom = "";
    sampdiv.style.height='90%';
    buttondiv.style.bottom = "0px";
    seldiv.style.height = "0px";
    seldiv.style.display = "none";
    linktext.innerHTML = "Show selected samples";
  }
} 

function select_category(category, study) {
  if(study != '') { 
    $('.study'+study+'.'+category).each(function() {this.checked = true;});
    count_update(study);
  }
  else { 
    $('.'+category).each(function() {this.checked = true;});
    for(i=0; i<STUDIES.length; i++) {
      count_update(STUDIES[i]);
    }
  }
}

function count_update(study) {
  var selected = $('#modal' + study + ' input:checkbox:checked').length;
  if(selected > 0) { $('#study' + study).addClass('success'); }
  else { $('#study' + study).removeClass('success'); }
}

function select_deselect(study, pdid, type, select) {
  boxes = '.study'+study+'.proc'+pdid
  if (type = '-sel') { boxes += '.-sel' }
  if(select == true) {
    $(boxes).each(function() {this.checked = true;});
  }
  else { 
    $(boxes).each(function() {this.checked = false;});
  }
  count_update(study);
}

function select_inverse(study, pdid, type) {
  boxes = '.study'+study+'.proc'+pdid
  if (type = '-sel') { boxes += '.-sel' }
  $(boxes).each(function() {
    if(this.checked == true) { this.checked = false; }
    else { this.checked = true; }
  });
}

function pre_submit(action) {
  document.getElementById('action').value = action;
  var msgdiv = document.getElementById('searchmsg');
  if(action == 'search') {
    msgdiv.style.color = '';
    msgdiv.style.align = 'center';
    msgdiv.innerHTML = '<img src="/static/img/waiting.gif"> <b>Searching...</b>';
    document.getElementById('results-div').hidden = true;
  } else if(action == 'continue') {
    var selected = $('#selected input:checkbox').length;
    if(selected == 0) {
      msgdiv.innerHTML = "Must select samples to continue!"
      return false;
    } else {
    document.getElementById('results-form').action = '/analysis/3'
    }
  } else if(action == "deselect") {
    var selected = $('#selected input:checkbox:checked').length;
    if(selected == 0) {
      msgdiv.innerHTML = "Must select samples to remove from study!"
      return false;
    }
  }
}

function add_metacat(metacat) {
  document.getElementById('query').value += (" " + metacat);
}

