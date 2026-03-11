<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=ISO-8859-1">
<style>
html, body {
	min-height: 100%;
	margin: 0;
	padding: 0;
}
body {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: flex-start;
	padding: 40px 20px;
	font-family: Arial, sans-serif;
	font-size: 1.4em;
	background: #f4f4f4;
	box-sizing: border-box;
}
#container {
	background: #fff;
	border: 1px solid #ccc;
	border-radius: 8px;
	padding: 40px 60px;
	box-shadow: 0 2px 12px rgba(0,0,0,0.12);
	min-width: 320px;
	width: 100%;
	max-width: 900px;
	box-sizing: border-box;
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
/* ── Search section ───────────────────────────────── */
#searchSection {
	margin-top: 32px;
	padding-top: 24px;
	border-top: 1px solid #e0e0e0;
}
#searchSection h2 {
	margin: 0 0 12px 0;
	font-size: 1em;
	color: #444;
}
#searchForm {
	display: flex;
	gap: 8px;
	flex-wrap: wrap;
	align-items: center;
}
#searchForm input[type="text"] {
	flex: 1;
	min-width: 180px;
	font-size: 1em;
	padding: 6px 8px;
}
#searchForm input[type="submit"] {
	font-size: 1em;
	padding: 6px 16px;
}
#searchError {
	margin-top: 10px;
	color: red;
	font-weight: bold;
}
#searchResults {
	margin-top: 16px;
	width: 100%;
	overflow-x: auto;
}
#searchResults table {
	width: 100%;
	border-collapse: collapse;
	font-size: 0.85em;
}
#searchResults th {
	background: #e8e8e8;
	padding: 6px 10px;
	text-align: left;
	border: 1px solid #ccc;
	white-space: nowrap;
}
#searchResults td {
	padding: 6px 10px;
	border: 1px solid #ddd;
	vertical-align: top;
}
#searchResults tr:nth-child(even) td {
	background: #f9f9f9;
}
#searchResults .no-results {
	color: #888;
	font-style: italic;
	margin-top: 8px;
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
// SQL Server connection settings for the SixBit database.
// Override via SIXBIT_SERVER / SIXBIT_DB environment variables if needed.
if (!defined('SIXBIT_SERVER')) {
	define('SIXBIT_SERVER', getenv('SIXBIT_SERVER') ?: 'SERVERWIN\\SIXBITDBSERVER');
}
if (!defined('SIXBIT_DB')) {
	define('SIXBIT_DB', getenv('SIXBIT_DB') ?: 'SixBit_BT_002');
}

// ── SQL search handler (GET) ───────────────────────────────────────────────
$searchQuery     = '';
$searchResults   = [];
$searchError     = '';
$searchPerformed = false;

if (isset($_GET['q']) && trim($_GET['q']) !== '') {
	$searchQuery     = trim($_GET['q']);
	$searchPerformed = true;

	if (!extension_loaded('sqlsrv')) {
		$searchError = 'The sqlsrv PHP extension is not loaded. '
		             . 'Please install the Microsoft SQL Server Driver for PHP.';
	} else {
		$connectionInfo = [
			'Database'               => SIXBIT_DB,
			'TrustServerCertificate' => true,
		];
		$conn = sqlsrv_connect(SIXBIT_SERVER, $connectionInfo);
		if ($conn === false) {
			$errs = sqlsrv_errors();
			$searchError = 'Database connection failed: '
			             . ($errs ? htmlspecialchars($errs[0]['message']) : 'Unknown error');
		} else {
			// Parameterized query – safe against SQL injection.
			$param  = '%' . $searchQuery . '%';
			$sql    = "SELECT TOP 50
			               ItemID,
			               Title,
			               SKU,
			               SellingPrice,
			               Quantity,
			               Status
			           FROM dbo.Listing
			           WHERE Title LIKE ?
			              OR SKU   LIKE ?
			              OR CAST(ItemID AS VARCHAR(20)) LIKE ?
			           ORDER BY Title";
			$params = [$param, $param, $param];
			$stmt   = sqlsrv_query($conn, $sql, $params);
			if ($stmt === false) {
				$errs = sqlsrv_errors();
				$searchError = 'Query failed: '
				             . ($errs ? htmlspecialchars($errs[0]['message']) : 'Unknown error');
			} else {
				while ($row = sqlsrv_fetch_array($stmt, SQLSRV_FETCH_ASSOC)) {
					$searchResults[] = $row;
				}
				sqlsrv_free_stmt($stmt);
			}
			sqlsrv_close($conn);
		}
	}
}
// ── End search handler ────────────────────────────────────────────────────

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

<!-- ── Search section ─────────────────────────────── -->
<div id="searchSection">
<h2>Search SixBit Database</h2>
<form id="searchForm" method="get" action="">
<input type="text" name="q" id="searchInput"
       placeholder="Title, SKU, or Item ID&hellip;"
       value="<?php echo htmlspecialchars($searchQuery)?>"
       autocomplete="off">
<input type="submit" value="Search">
</form>

<?php if ($searchError): ?>
<div id="searchError"><?php echo htmlspecialchars($searchError)?></div>
<?php elseif ($searchPerformed && count($searchResults) === 0): ?>
<div id="searchResults"><p class="no-results">No results found for &ldquo;<?php echo htmlspecialchars($searchQuery)?>&rdquo;.</p></div>
<?php elseif (count($searchResults) > 0): ?>
<div id="searchResults">
<table>
<thead>
<tr>
<th>Item ID</th>
<th>Title</th>
<th>SKU</th>
<th>Price</th>
<th>Qty</th>
<th>Status</th>
</tr>
</thead>
<tbody>
<?php foreach ($searchResults as $row): ?>
<tr>
<td><?php echo htmlspecialchars((string)$row['ItemID'])?></td>
<td><?php echo htmlspecialchars((string)$row['Title'])?></td>
<td><?php echo htmlspecialchars((string)$row['SKU'])?></td>
<td><?php echo htmlspecialchars((string)$row['SellingPrice'])?></td>
<td><?php echo htmlspecialchars((string)$row['Quantity'])?></td>
<td><?php echo htmlspecialchars((string)$row['Status'])?></td>
</tr>
<?php endforeach?>
</tbody>
</table>
</div>
<?php endif?>

</div>
<!-- ── End search section ─────────────────────────── -->

</div>
</body>
</html>
