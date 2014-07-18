function toggle_row(sid, select) {
  if(select) {
    var row_style = document.getElementById("selrow" + sid).style;
    var toggle = document.getElementById("seltoggle" + sid);
  }
  else {
    var row_style = document.getElementById("row" + sid).style;
    var toggle = document.getElementById("toggle" + sid);
  }
  if(row_style.display == "none") {
    row_style.display = '';
    toggle.innerHTML = "(-)";
  }
  else {
    row_style.display = "none";
    toggle.innerHTML = "(+)";
  }
} 

function select_category(category, study) {
  if(study != '') { 
    $('.'+study+'.'+category).each(function() {this.checked = true;});
  }
  else { 
    $('.'+category).each(function() {this.checked = true;});
  }
}

function enable_study_datatype(id) {
  document.getElementById(id).disabled=false;
}

function pre_submit(action) {
  document.getElementById('action').value = action;
  if(action == 'continue') {document.getElementById('results-form').action = '/analysis/3'}
}
