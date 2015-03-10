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
  if(study !== '') { 
    $('.study'+study+'.'+category).each(function() {this.checked = true;});
    count_update(study, '');
  }
  else { 
    $('.'+category).each(function() {this.checked = true;});
    for(i=0; i<STUDIES.length; i++) {
      count_update(STUDIES[i], '');
    }
  }
}

function count_update(study, sel) {
  format = '#modal' + study;
  if(sel === "-sel") { format = format + "-sel"; }
    format = format + ' input:checkbox:checked';
  var selected = $(format).length;
  if(selected > 0 && sel !== "-sel") { $('#study' + study).addClass('success'); }
  else if(sel !== "-sel") { $('#study' + study).removeClass('success'); }
  else if(selected > 0 && sel === "-sel") { $('#study' + study+"-sel").addClass('danger'); }
  else if(sel === "-sel") { $('#study' + study + "-sel").removeClass('danger'); }
}

function select_deselect(study, filter, sel, select) {
  filter = '.study' + study + filter;
  if(sel == '-sel') { filter = filter + '.-sel'; }
  if(select === true) {
    $(filter).each(function() {this.checked = true;});
  }
  else { 
    $(filter).each(function() {this.checked = false;});
  }
  count_update(study, sel);
}

function select_inverse(study, filter, sel, type) {
  filter = filter + ".study" + study;
  if(sel === "-sel") { filter += ".-sel"; }
  $(filter).each(function() {
    if(this.checked === true) { this.checked = false; }
    else { this.checked = true; }
  });
  count_update(study, sel);
}

function pre_submit(action) {
  document.getElementById('action').value = action;
  var msgdiv = document.getElementById('searchmsg');
  if(action === 'search') {
    msgdiv.style.color = '';
    msgdiv.style.align = 'center';
    msgdiv.innerHTML = '<img src="/static/img/waiting.gif"> <b>Searching...</b>';
    document.getElementById('results-div').hidden = true;
  } else if(action === 'continue') {
    var selected = $('#selected input:checkbox').length;
    if(selected === 0) {
      msgdiv.innerHTML = "Must select samples to continue!";
      return false;
    } else {
    document.getElementById('results-form').action = '/analysis/3';
    }
  } else if(action == "deselect") {
    var selected = $('#selected input:checkbox:checked').length;
    if(selected === 0) {
      msgdiv.innerHTML = "Must select samples to remove from study!";
      return false;
    }
  }
}

function add_metacat(metacat) {
  document.getElementById('query').value += (" " + metacat);
}

