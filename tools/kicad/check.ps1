[CmdletBinding()]
param(
    [string]$Project = "hardware/unit-board/unit-board",
    [string]$OutputDirectory = (Join-Path $env:TEMP "differential-swerve-kicad-check"),
    [switch]$FailOnViolations
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
$schematic = "$projectBase.kicad_sch"
$board = "$projectBase.kicad_pcb"

if (-not (Test-Path -LiteralPath $schematic)) {
    throw "Schematic not found: $schematic"
}

New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
$projectName = [IO.Path]::GetFileName($projectBase)
$ercReport = Join-Path $OutputDirectory "$projectName-erc.rpt"
$schematicPdf = Join-Path $OutputDirectory "$projectName-schematic.pdf"

$ercArguments = @("sch", "erc", "--output", $ercReport)
if ($FailOnViolations) {
    $ercArguments += "--exit-code-violations"
}
$ercArguments += $schematic

& $kicadCli @ercArguments
if ($LASTEXITCODE -ne 0) {
    throw "Schematic ERC failed with exit code $LASTEXITCODE. Report: $ercReport"
}

& $kicadCli sch export pdf --output $schematicPdf $schematic
if ($LASTEXITCODE -ne 0) {
    throw "Schematic PDF export failed with exit code $LASTEXITCODE."
}

$outputs = @($ercReport, $schematicPdf)

if (Test-Path -LiteralPath $board) {
    $drcReport = Join-Path $OutputDirectory "$projectName-drc.rpt"
    $drcArguments = @("pcb", "drc", "--output", $drcReport)
    if ($FailOnViolations) {
        $drcArguments += "--exit-code-violations"
    }
    $drcArguments += $board

    & $kicadCli @drcArguments
    if ($LASTEXITCODE -ne 0) {
        throw "PCB DRC failed with exit code $LASTEXITCODE. Report: $drcReport"
    }
    $outputs += $drcReport
}

Write-Host "KiCad checks completed with $(& $kicadCli version)."
$outputs | ForEach-Object { Write-Host "  $_" }
