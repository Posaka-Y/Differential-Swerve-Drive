[CmdletBinding()]
param(
    [string]$Project = "hardware/unit-board/unit-board",
    [string]$OutputDirectory = "output/fabrication/unit-board-revA",
    [ValidateRange(1, 100)]
    [int]$ProcurementBoards = 4
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
$cliCandidates = @(@(
    (Get-Command kicad-cli -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -First 1),
    "C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"
) | Where-Object { $_ -and (Test-Path -LiteralPath $_) })

if (-not $cliCandidates) {
    throw "kicad-cli was not found. Install KiCad 10 or add its bin directory to PATH."
}

$kicadCli = $cliCandidates[0]
$projectBase = if ([IO.Path]::IsPathRooted($Project)) {
    $Project
} else {
    Join-Path $repositoryRoot $Project
}
$board = "$projectBase.kicad_pcb"
$schematic = "$projectBase.kicad_sch"

if (-not (Test-Path -LiteralPath $board)) {
    throw "Board not found: $board"
}
if (-not (Test-Path -LiteralPath $schematic)) {
    throw "Schematic not found: $schematic"
}

$resolvedOutput = if ([IO.Path]::IsPathRooted($OutputDirectory)) {
    $OutputDirectory
} else {
    Join-Path $repositoryRoot $OutputDirectory
}

if ((Test-Path -LiteralPath $resolvedOutput) -and
    (Get-ChildItem -LiteralPath $resolvedOutput -Force | Select-Object -First 1)) {
    throw "Output directory is not empty: $resolvedOutput"
}

$gerberDirectory = Join-Path $resolvedOutput "gerber"
$drillDirectory = Join-Path $resolvedOutput "drill"
New-Item -ItemType Directory -Path $gerberDirectory, $drillDirectory -Force | Out-Null

& $kicadCli pcb drc --exit-code-violations --output (Join-Path $resolvedOutput "unit-board-drc.rpt") $board
if ($LASTEXITCODE -ne 0) {
    throw "DRC failed; fabrication files were not generated."
}

& $kicadCli sch export bom --output (Join-Path $resolvedOutput "unit-board-jlcpcb-bom.csv") `
    --fields "Value,Reference,Footprint,LCSC Part #,Manufacturer_Name,Manufacturer_Part_Number,QUANTITY" `
    --labels "Comment,Designator,Footprint,LCSC Part #,Manufacturer,Manufacturer Part Number,Quantity" `
    --group-by "Value,Footprint,LCSC Part #,Manufacturer_Name,Manufacturer_Part_Number" `
    --sort-field Reference --exclude-dnp --ref-range-delimiter="" $schematic
if ($LASTEXITCODE -ne 0) {
    throw "BOM export failed."
}

& (Join-Path $PSScriptRoot "digikey-bom.ps1") `
    -Boards $ProcurementBoards `
    -Profile Build `
    -BaseBom (Join-Path $resolvedOutput "unit-board-jlcpcb-bom.csv") `
    -OutputDirectory $resolvedOutput
if ($LASTEXITCODE -ne 0) {
    throw "DigiKey procurement BOM export failed."
}

& (Join-Path $PSScriptRoot "digikey-bom.ps1") `
    -Boards $ProcurementBoards `
    -Profile LabStock `
    -BaseBom (Join-Path $resolvedOutput "unit-board-jlcpcb-bom.csv") `
    -OutputDirectory $resolvedOutput
if ($LASTEXITCODE -ne 0) {
    throw "DigiKey lab-stock BOM export failed."
}

$layers = "F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,F.Mask,B.Mask,F.SilkS,B.SilkS,Edge.Cuts"
& $kicadCli pcb export gerbers --output $gerberDirectory --layers $layers --check-zones $board
if ($LASTEXITCODE -ne 0) {
    throw "Gerber export failed."
}

& $kicadCli pcb export drill --output $drillDirectory --format excellon --excellon-units mm `
    --excellon-zeros-format decimal --excellon-separate-th --generate-map --map-format pdf `
    --generate-report --report-path (Join-Path $drillDirectory "unit-board-drill-report.rpt") $board
if ($LASTEXITCODE -ne 0) {
    throw "Drill export failed."
}

& $kicadCli pcb export ipcd356 --output (Join-Path $resolvedOutput "unit-board.ipc") $board
if ($LASTEXITCODE -ne 0) {
    throw "IPC-D-356 export failed."
}

& $kicadCli pcb export pos --output (Join-Path $resolvedOutput "unit-board-position.csv") `
    --side both --format csv --units mm --exclude-dnp $board
if ($LASTEXITCODE -ne 0) {
    throw "Position export failed."
}

& $kicadCli pcb export stats --output (Join-Path $resolvedOutput "unit-board-statistics.txt") $board
if ($LASTEXITCODE -ne 0) {
    throw "Board statistics export failed."
}

& $kicadCli pcb export step --output (Join-Path $resolvedOutput "unit-board.step") `
    --force --no-dnp --subst-models $board
if ($LASTEXITCODE -ne 0) {
    throw "STEP export failed."
}

$archivePath = "$resolvedOutput.zip"
if (Test-Path -LiteralPath $archivePath) {
    throw "Archive already exists: $archivePath"
}
Compress-Archive -Path (Join-Path $resolvedOutput "*") -DestinationPath $archivePath

Write-Host "Fabrication package created:"
Write-Host "  $resolvedOutput"
Write-Host "  $archivePath"
