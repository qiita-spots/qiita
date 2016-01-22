// 2006-08-21 - Created
// 2006-11-05 - Modified - head and body
function addColumn(tblId, header, values)
{
	var tblHeadObj = document.getElementById(tblId).tHead;
	for (var h=0; h<tblHeadObj.rows.length; h++) {
		var newTH = document.createElement('th');
		tblHeadObj.rows[h].appendChild(newTH);
		newTH.innerHTML = header;
	}

	var tblBodyObj = document.getElementById(tblId).tBodies[0];
	for (var i=0; i<tblBodyObj.rows.length; i++) {
		var newCell = tblBodyObj.rows[i].insertCell(-1);
		newCell.innerHTML = values[i];
	}
}
function deleteColumn(tblId, col)
{
	var allRows = document.getElementById(tblId).rows;
	for (var i=0; i<allRows.length; i++) {
		allRows[i].deleteCell(col);
	}
}