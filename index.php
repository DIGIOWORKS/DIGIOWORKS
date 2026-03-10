<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=ISO-8859-1">
<style>
html, body {
	height: 100%;
	margin: 0;
	padding: 0;
}
body {
	display: flex;
	align-items: center;
	justify-content: center;
	font-family: Arial, sans-serif;
	font-size: 1.4em;
	background: #f4f4f4;
}
#container {
	background: #fff;
	border: 1px solid #ccc;
	border-radius: 8px;
	padding: 40px 60px;
	box-shadow: 0 2px 12px rgba(0,0,0,0.12);
	min-width: 320px;
}
#container form input[type="text"] {
	font-size: 1em;
	padding: 6px 8px;
	width: 220px;
}
#container form input[type="submit"] {
	font-size: 1em;
	padding: 6px 16px;
	margin-top: 10px;
}
#message {
	margin-top: 12px;
	font-weight: bold;
}
#printButtonBox {
	margin-top: 16px;
}
</style>
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
window.onload = resetFocus;
</script>
<title>Inventory</title>
</head>
<body>
<!-- form processing -->
<?php 
include 'print.php';
$message = "";
$printMessage = "";
$messageColor = "red";
$itemId = "";
if (count($_POST) > 0) {
	
	if (!empty($_POST["print"])) {
		if (!(empty($_POST["itemId"]))) {
			$itemId = $_POST["itemId"];
			if (ctype_digit($itemId)) {
				$printMessage = printLabel($itemId, "printer.csv");
			}
			else {
				$printMessage = "Invalid ItemID to print!";
			}
		}
		else {
			$printMessage = "No ItemID to print!";
		}
	}
	
	else if (!(empty($_POST["itemId"]) || empty($_POST["location"]))) {
		$itemId = $_POST["itemId"];
		// Strip CSV metacharacters (newlines, tabs, carriage returns) from location
		$location = str_replace(array("\n", "\r", "\t"), '', $_POST["location"]);
		if (ctype_digit($itemId)) {
			$printVisible = "display:block";
			//append to inventory.csv
			$file = fopen("inventory.csv", 'a');
			if ($file === false) {
				$message = "There was an error opening the inventory file!";
			}
			else if (fwrite($file, $itemId . "\t" . $location . "\n")) {
				$messageColor = "black";
				$message = "Added: ItemID: " . $itemId . ";  Location: " . $location;
				$hfile = fopen("inventory-history.csv", 'a');
				if ($hfile !== false) {
					fwrite($hfile, $itemId . "\t" . $location . "\n");
					fclose($hfile);
				}
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
<div id="container">
<form id="inputForm" method="post">
&nbsp; ItemID: <input id="itemIdInput" type="text" name="itemId" value="" oninput="itemIdChanged(this)"><br><br>
Location: <input id="locationInput" type="text" name="location" value="" oninput="locationChanged(this)"><br>
<input type="submit" value="Submit" onFocus="submitForm()">
</form> 
<div id="message" style="color:<?php echo $messageColor?>">
<?php echo $message?>
</div>
<div id="printButtonBox">
<form id="printForm" method="post">
<input id="print" name="print" type="hidden" value="true" style="display:none">
<input id="itemIdPrint" name="itemId" type="text" value="<?php echo htmlspecialchars($itemId)?>">
<input type="submit" value="Print">
</form>
<?php echo $printMessage?>
</div>
</div>
</body>
</html>
