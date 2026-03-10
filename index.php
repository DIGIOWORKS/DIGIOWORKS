<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=ISO-8859-1">
<script type="text/javascript">
var debounceTimer;
var itemIdDebounceTimer;
function itemIdChanged(field) {
	clearTimeout(itemIdDebounceTimer);
	if (field.value.length >= 5) {
		itemIdDebounceTimer = setTimeout(function() {
			document.getElementById('locationInput').focus();
		}, 500);
	}
}
function locationChanged(field) {
	clearTimeout(debounceTimer);
	if (field.value.length >= 4) {
		debounceTimer = setTimeout(submitForm, 500);
	}
}
function resetFocus() {
	document.getElementById('itemIdInput').focus();
}
function submitForm() {
	document.forms["inputForm"].submit();
}
window.onload = resetFocus();
</script>
<title>Inventory</title>
</head>
<body onload = "resetFocus();">
<!-- form processing -->
<?php 
include 'print.php';
$message = "";
$printMessage = "";
$messageColor = "red";
if (count($_POST) > 0) {
	
	if (!empty($_POST["print"])) {
		if (!(empty($_POST["itemId"]))) {
			$itemId = $_POST["itemId"];
			$printMessage = printLabel($itemId, "printer.csv");
		}
		else {
			$printMessage = "No ItemID to print!";
		}
	}
	
	else if (!(empty($_POST["itemId"]) || empty($_POST["location"]))) {
		$itemId = $_POST["itemId"];
		$location = $_POST["location"];
		if (ctype_digit($itemId)) {
			$printVisible = "display:block";
			//append to inventory.csv
			$file = fopen("inventory.csv", 'a');
			if (fwrite($file, $itemId . "\t" . $location . "\n")) {
				$messageColor = "black";
				$message = "Added: ItemID: " . $itemId . ";  Location: " . $location;
			}
			else {
				$message = "There was an error writing the new data!";
			}
			fclose($file);
		}
		else {
			$message = "Invalid ItemID";
		}
	}
	else {
		$message = "Error: Form incomplete.";
	}
}
?>
<div style="margin:auto; border:1px solid black; position:relative">
<form id="inputForm" method="post">
&nbsp; ItemID: <input id="itemIdInput" type="text"  name="itemId" value="" oninput="itemIdChanged(this)"><br>
Location: <input id="locationInput" type="text" name="location" value="" oninput="locationChanged(this)"><br>
<input type="submit" value="Submit" onFocus="submitForm()">
</form> 
<div id="message" style="color:<?php echo $messageColor?>">
<?php echo $message?>
</div>
<div id="printButtonBox">
<form id="printForm" method="post">
<input id="print" name="print" "type="hidden" value="true" style="display:none">
<input id="itemId" name="itemId" "type="text" value="<?php echo $itemId?>">
<input type="submit" value="Print">
</form>
<?php echo $printMessage?>
</div>
</div>
</body>
</html>
