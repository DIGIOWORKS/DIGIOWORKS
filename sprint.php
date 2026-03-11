<?php
/**
 * sprint.php
 *
 * Provides printLabel() to print an inventory item label with a Code-128
 * barcode on the DYMO LabelWriter 400 shared at \\w530pc.
 *
 * Requirements (server-side):
 *  - DYMO Label Software or DYMO Connect for Desktop installed on the
 *    Windows machine running PHP (supplies DYMO.Label.Framework.dll).
 *  - PHP exec() enabled in php.ini.
 *  - The web-server user must have print access to \\w530pc\DYMO LabelWriter 400.
 */

define('DYMO_PRINTER_NAME', 'DYMO LabelWriter 400');
define('DYMO_PRINTER_UNC',  '\\\\w530pc\\DYMO LabelWriter 400');

/**
 * Print a label for the given item ID.
 *
 * Looks up an optional description in the tab-delimited $csvFile
 * (format: ItemID<TAB>Description per line), builds a DYMO label XML
 * with the item ID as text and as a Code-128 barcode, then sends the
 * job to the DYMO LabelWriter 400 via PowerShell.
 *
 * @param  string $itemId  Numeric item ID.
 * @param  string $csvFile Path to tab-delimited file for description lookup.
 * @return string          Human-readable status or error message.
 */
function printLabel($itemId, $csvFile) {
    $description = getItemDescription($itemId, $csvFile);
    $labelXml    = buildLabelXml($itemId, $description);
    return sendToPrinter($itemId, $labelXml);
}

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

/**
 * Return the description for $itemId from the tab-delimited $csvFile,
 * or '' if the file is missing or the item is not found.
 */
function getItemDescription($itemId, $csvFile) {
    if (!file_exists($csvFile)) {
        return '';
    }
    $fh = @fopen($csvFile, 'r');
    if ($fh === false) {
        return '';
    }
    $desc = '';
    while (($row = fgetcsv($fh, 0, "\t")) !== false) {
        if (isset($row[0]) && trim($row[0]) === trim($itemId)) {
            $desc = isset($row[1]) ? trim($row[1]) : '';
            break;
        }
    }
    fclose($fh);
    return $desc;
}

/**
 * Build a DYMO label XML string.
 *
 * Label: 30252 Address (3.5" × 1.125", landscape).
 *   – Top area    : Item ID and optional description (bold text).
 *   – Bottom area : Code-128 barcode of the item ID with number below.
 */
function buildLabelXml($itemId, $description = '') {
    $safeId   = htmlspecialchars($itemId,      ENT_XML1 | ENT_QUOTES, 'UTF-8');
    $safeDesc = htmlspecialchars($description, ENT_XML1 | ENT_QUOTES, 'UTF-8');
    $labelLine = ($description !== '')
        ? "Item ID: {$safeId}  {$safeDesc}"
        : "Item ID: {$safeId}";

    return <<<XML
<?xml version="1.0" encoding="utf-8"?>
<DieCutLabel Version="8.0" Units="twips">
  <PaperOrientation>Landscape</PaperOrientation>
  <Id>Address</Id>
  <PaperName>30252 Address</PaperName>
  <DrawCommands/>
  <ObjectInfo>
    <TextObject>
      <Name>ItemText</Name>
      <ForeColor Alpha="255" Red="0" Green="0" Blue="0"/>
      <BackColor Alpha="0" Red="255" Green="255" Blue="255"/>
      <LinkedObjectName/>
      <Rotation>Rotation0</Rotation>
      <IsMirrored>False</IsMirrored>
      <IsVariable>False</IsVariable>
      <HorizontalAlignment>Left</HorizontalAlignment>
      <VerticalAlignment>Middle</VerticalAlignment>
      <TextFitMode>ShrinkToFit</TextFitMode>
      <UseFullFontHeight>True</UseFullFontHeight>
      <Verticalized>False</Verticalized>
      <StyledText>
        <Element>
          <String>{$labelLine}</String>
          <Attributes>
            <Font Family="Arial" Size="10" Bold="True" Italic="False" Underline="False" StrikeOut="False"/>
            <ForeColor Alpha="255" Red="0" Green="0" Blue="0"/>
          </Attributes>
        </Element>
      </StyledText>
    </TextObject>
    <Bounds X="331" Y="0" Width="4709" Height="540"/>
  </ObjectInfo>
  <ObjectInfo>
    <BarcodeObject>
      <Name>ItemBarcode</Name>
      <ForeColor Alpha="255" Red="0" Green="0" Blue="0"/>
      <BackColor Alpha="0" Red="255" Green="255" Blue="255"/>
      <LinkedObjectName/>
      <Rotation>Rotation0</Rotation>
      <IsMirrored>False</IsMirrored>
      <IsVariable>False</IsVariable>
      <Text>{$safeId}</Text>
      <Type>Code128Auto</Type>
      <Size>Small</Size>
      <TextPosition>Bottom</TextPosition>
      <TextFont>
        <Family>Arial</Family>
        <Size>8</Size>
        <Bold>False</Bold>
        <Italic>False</Italic>
        <Underline>False</Underline>
        <StrikeOut>False</StrikeOut>
      </TextFont>
      <CheckSumEnabled>False</CheckSumEnabled>
      <BarcodeAlignment>Center</BarcodeAlignment>
    </BarcodeObject>
    <Bounds X="331" Y="540" Width="4709" Height="1080"/>
  </ObjectInfo>
</DieCutLabel>
XML;
}

/**
 * Write the label XML to a temp file, run a PowerShell script that loads
 * the DYMO Label Framework DLL and sends the job to the printer, then
 * remove the temp files.
 *
 * @return string Status message.
 */
function sendToPrinter($itemId, $labelXml) {
    $tmpDir    = sys_get_temp_dir();
    $labelFile = tempnam($tmpDir, 'dymo_label_');
    $psFile    = tempnam($tmpDir, 'dymo_ps_');

    if ($labelFile === false || file_put_contents($labelFile, $labelXml) === false) {
        return 'Error: Could not write temporary label file.';
    }

    if ($psFile === false || file_put_contents($psFile, buildPowerShellScript($labelFile)) === false) {
        @unlink($labelFile);
        return 'Error: Could not write temporary PowerShell script.';
    }

    $out        = [];
    $returnCode = 0;
    exec(
        'powershell.exe -ExecutionPolicy Bypass -NonInteractive -NoProfile -File '
            . escapeshellarg($psFile) . ' 2>&1',
        $out,
        $returnCode
    );

    @unlink($labelFile);
    @unlink($psFile);

    if ($returnCode === 0) {
        return 'Label printed for Item ID: ' . htmlspecialchars($itemId);
    }

    $detail = trim(implode(' | ', array_filter($out)));
    return 'Print error: ' . htmlspecialchars($detail ?: 'Exit code ' . $returnCode);
}

/**
 * Build the PowerShell script that:
 *  1. Installs the shared network printer if not already mapped.
 *  2. Locates the DYMO Label Framework DLL.
 *  3. Opens the label XML and prints it via the DYMO Framework API.
 *
 * PHP variables are injected only in the dynamic header block;
 * the remainder uses a nowdoc so PowerShell syntax passes through unchanged.
 */
function buildPowerShellScript($labelFilePath) {
    // Escape single quotes for PowerShell single-quoted strings.
    $psLabelFile   = str_replace("'", "''", $labelFilePath);
    $psPrinterName = str_replace("'", "''", DYMO_PRINTER_NAME);
    $psPrinterUNC  = str_replace("'", "''", DYMO_PRINTER_UNC);

    // Dynamic variable assignments (PHP interpolates the values here).
    $header = "\$ErrorActionPreference = 'Stop'\n"
            . "\$printerName = '$psPrinterName'\n"
            . "\$printerUNC  = '$psPrinterUNC'\n"
            . "\$labelFile   = '$psLabelFile'\n";

    // Static script body – nowdoc prevents PHP from interpreting $ signs.
    $body = <<<'POWERSHELL'

# ── 1. Ensure the shared printer is installed on this machine ─────────────
$installed = (Get-Printer -ErrorAction SilentlyContinue |
              Select-Object -ExpandProperty Name)
if ($installed -notcontains $printerName) {
    try {
        Add-Printer -ConnectionName $printerUNC -ErrorAction Stop
    } catch {
        Write-Warning "Could not add printer: $_"
    }
}

# ── 2. Locate the DYMO Label Framework DLL ───────────────────────────────
$dllCandidates = @(
    "${env:ProgramFiles(x86)}\DYMO\DYMO Label Software\Framework\DYMO.Label.Framework.dll",
    "${env:ProgramFiles}\DYMO\DYMO Label Software\Framework\DYMO.Label.Framework.dll",
    "${env:ProgramFiles(x86)}\DYMO\DYMO Connect\DYMO.Label.Framework.dll",
    "${env:ProgramFiles}\DYMO\DYMO Connect\DYMO.Label.Framework.dll"
)

$dllPath = $null
foreach ($c in $dllCandidates) {
    if (Test-Path $c) { $dllPath = $c; break }
}
if (-not $dllPath) {
    throw 'DYMO Label Framework DLL not found. Install DYMO Label Software on this machine.'
}

# ── 3. Print via the DYMO Label Framework API ────────────────────────────
Add-Type -Path $dllPath
[Dymo.Label.Framework.Framework]::Init()

$xml   = Get-Content -Path $labelFile -Raw -Encoding UTF8
$label = [Dymo.Label.Framework.Label]::Open($xml)

$printers = [Dymo.Label.Framework.Framework]::GetLabelWriterPrinters()
$target   = $printers |
            Where-Object { $_.Name -like '*LabelWriter 400*' } |
            Select-Object -First 1
if (-not $target) { $target = $printers | Select-Object -First 1 }
if (-not $target) { throw 'No DYMO LabelWriter printer found.' }

$label.Print($target.Name, $null, $null)
Write-Output "SUCCESS: printed to $($target.Name)"
POWERSHELL;

    return $header . $body;
}
