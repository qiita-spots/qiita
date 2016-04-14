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
    $('.'+study+'.'+category).each(function() {this.checked = true;});
    count_update(study);
  }
  else {
    $('.'+category).each(function() {this.checked = true;});
    for(i=0; i<STUDIES.length; i++) {
      count_update(STUDIES[i]);
    }
  }
}

function select_deselect_samples_study(study) {
  var selected_datatypes = $('#study' + study + ' input:checkbox:checked').length;
  var sel = false;
  if (selected_datatypes > 0) { sel = true; }
  select_deselect(study, sel)
}

function count_update(study) {
  var selected = $('#modal' + study + ' input:checkbox:checked').length;
  var studylink = document.getElementById('modal-link-' + study)
  document.getElementById('count' + study).innerHTML = selected;
  if(selected > 0) {
    $('#study' + study).addClass('success');
    studylink.disabled = false;
    studylink.style = "";
  }
  else {
    $('#study' + study).removeClass('success');
    studylink.disabled = true;
    studylink.style = "text-decoration: none;";
    $('#study' + study + " input:checkbox").each(function() {this.checked = false;})
  }
}

function select_deselect(study, select) {
  if(select == true) {
    $('.'+study).each(function() {this.checked = true;});
  }
  else {
    $('.'+study).each(function() {this.checked = false;});
  }
  count_update(study);
}

function select_inverse(study) {
  $('.'+study).each(function() {
    if(this.checked == true) { this.checked = false; }
    else { this.checked = true; }
  });
}
