param(
    [string]$ProjectDirectory = "hardware/central-board"
)

$ErrorActionPreference = "Stop"
$repoRoot = (Get-Location).Path
$projectPath = if ([System.IO.Path]::IsPathRooted($ProjectDirectory)) {
    $ProjectDirectory
} else {
    Join-Path $repoRoot $ProjectDirectory
}
$modulePath = Join-Path $projectPath "modules"
$flatPath = Join-Path $projectPath ".central-board-flat.tmp.sch"

New-Item -ItemType Directory -Force -Path $projectPath, $modulePath | Out-Null

# The detailed circuit content remains in one deterministic source generator.
# This wrapper partitions that output into responsibility-based sheets.
& (Join-Path $PSScriptRoot "generate-central-board-schematic.ps1") -OutputPath $flatPath

$source = [System.IO.File]::ReadAllLines($flatPath)

$definitions = [ordered]@{
    power = [pscustomobject]@{
        File = "100-power.sch"; Title = "100 Power Input and 5V Distribution"
        XMin = 0; XMax = 3899; YMin = 0; YMax = 4999; DX = 0; DY = 0
    }
    teensy = [pscustomobject]@{
        File = "200-teensy.sch"; Title = "200 Teensy 4.1 Carrier and Safety GPIO"
        XMin = 3900; XMax = 6799; YMin = 0; YMax = 4999; DX = -3400; DY = 0
    }
    can = [pscustomobject]@{
        File = "300-can.sch"; Title = "300-500 CAN Communication"
        XMin = 6800; XMax = 20000; YMin = 0; YMax = 4999; DX = -6300; DY = 0
    }
    safety = [pscustomobject]@{
        File = "600-safety.sch"; Title = "600 E-stop and Contactor Safety"
        XMin = 0; XMax = 6299; YMin = 5000; YMax = 20000; DX = 0; DY = -4700
    }
    monitor = [pscustomobject]@{
        File = "700-monitoring.sch"; Title = "700 Battery and Motor Power Monitoring"
        XMin = 6300; XMax = 9599; YMin = 5000; YMax = 20000; DX = -5800; DY = -4700
    }
    expansion = [pscustomobject]@{
        File = "800-expansion.sch"; Title = "800 Expansion and Test Access"
        XMin = 9600; XMax = 20000; YMin = 5000; YMax = 20000; DX = -9000; DY = -4700
    }
}

function Get-ModuleForPoint([int]$X, [int]$Y) {
    foreach ($entry in $definitions.GetEnumerator()) {
        $d = $entry.Value
        if ($X -ge $d.XMin -and $X -le $d.XMax -and $Y -ge $d.YMin -and $Y -le $d.YMax) {
            return $entry.Key
        }
    }
    throw "No module region for point ($X,$Y)"
}

function Move-EntityLine([string]$Line, [int]$DX, [int]$DY) {
    if ($Line -match '^P\s+(-?\d+)\s+(-?\d+)$') {
        return "P $([int]$Matches[1] + $DX) $([int]$Matches[2] + $DY)"
    }
    if ($Line -match '^(F\s+\d+\s+".*?"\s+[HV]\s+)(-?\d+)\s+(-?\d+)(\s+.*)$') {
        return "$($Matches[1])$([int]$Matches[2] + $DX) $([int]$Matches[3] + $DY)$($Matches[4])"
    }
    if ($Line -match '^\s+1\s+(-?\d+)\s+(-?\d+)\s*$') {
        return "`t1    $([int]$Matches[1] + $DX) $([int]$Matches[2] + $DY)"
    }
    if ($Line -match '^\s*(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s*$') {
        if ([Math]::Abs([int]$Matches[1]) -le 1 -and
            [Math]::Abs([int]$Matches[2]) -le 1 -and
            [Math]::Abs([int]$Matches[3]) -le 1 -and
            [Math]::Abs([int]$Matches[4]) -le 1) {
            return $Line
        }
        return "`t$([int]$Matches[1] + $DX) $([int]$Matches[2] + $DY) $([int]$Matches[3] + $DX) $([int]$Matches[4] + $DY)"
    }
    if ($Line -match '^(Text\s+(?:Label|Notes)\s+)(-?\d+)\s+(-?\d+)(\s+.*)$') {
        return "$($Matches[1])$([int]$Matches[2] + $DX) $([int]$Matches[3] + $DY)$($Matches[4])"
    }
    return $Line
}

$entities = foreach ($key in $definitions.Keys) {
    $list = [System.Collections.Generic.List[object]]::new()
    [pscustomobject]@{ Key = $key; Items = $list }
}
$entityMap = @{}
foreach ($item in $entities) { $entityMap[$item.Key] = $item.Items }

$index = 0
while ($index -lt $source.Count) {
    $line = $source[$index]
    if ($line -eq '$Comp') {
        $block = [System.Collections.Generic.List[string]]::new()
        $x = $null; $y = $null
        do {
            $block.Add($source[$index])
            if ($source[$index] -match '^P\s+(-?\d+)\s+(-?\d+)$') {
                $x = [int]$Matches[1]; $y = [int]$Matches[2]
            }
            $done = $source[$index] -eq '$EndComp'
            $index++
        } while (-not $done)
        $key = Get-ModuleForPoint $x $y
        $entityMap[$key].Add($block.ToArray())
        continue
    }
    if ($line -eq 'Wire Wire Line') {
        $coords = $source[$index + 1]
        if ($coords -notmatch '^\s*(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)') {
            throw "Malformed wire at source line $index"
        }
        $key = Get-ModuleForPoint ([int]$Matches[1]) ([int]$Matches[2])
        $entityMap[$key].Add(@($line, $coords))
        $index += 2
        continue
    }
    if ($line -match '^Text\s+(Label|Notes)\s+(-?\d+)\s+(-?\d+)') {
        $key = Get-ModuleForPoint ([int]$Matches[2]) ([int]$Matches[3])
        $entityMap[$key].Add(@($line, $source[$index + 1]))
        $index += 2
        continue
    }
    $index++
}

function New-SchematicHeader([string]$Title, [int]$SheetNumber) {
    return @(
        'EESchema Schematic File Version 4',
        'LIBS:power',
        'LIBS:device',
        'LIBS:Connector_Generic',
        'LIBS:Switch',
        'LIBS:Transistor_FET',
        'EELAYER 29 0',
        'EELAYER END',
        '$Descr A4 11693 8268',
        'encoding utf-8',
        "Sheet $SheetNumber 7",
        "Title `"$Title`"",
        'Date "2026-08-04"',
        'Rev "A - HUMAN REVIEW DRAFT"',
        'Comp "Differential Swerve"',
        'Comment1 "Responsibility-based hierarchical schematic"',
        'Comment2 "Global labels connect modules"',
        '$EndDescr'
    )
}

$sheetNo = 2
foreach ($entry in $definitions.GetEnumerator()) {
    $key = $entry.Key
    $d = $entry.Value
    $out = [System.Collections.Generic.List[string]]::new()
    foreach ($headerLine in (New-SchematicHeader $d.Title $sheetNo)) { $out.Add($headerLine) }
    foreach ($entity in $entityMap[$key]) {
        foreach ($entityLine in $entity) {
            $out.Add((Move-EntityLine $entityLine $d.DX $d.DY))
        }
    }
    $out.Add('$EndSCHEMATC')
    [System.IO.File]::WriteAllLines((Join-Path $modulePath $d.File), $out, [System.Text.UTF8Encoding]::new($false))
    $sheetNo++
}

$root = [System.Collections.Generic.List[string]]::new()
foreach ($line in (New-SchematicHeader 'Teensy 4.1 Central Board - Module Index' 1)) { $root.Add($line) }
$root.Add('Text Notes 700 650 0    90   ~ 18')
$root.Add('CENTRAL BOARD RESPONSIBILITY MAP')
$root.Add('Text Notes 700 900 0    50   ~ 12')
$root.Add('Open each child sheet and review its inputs, outputs, protection and TBD gates independently.')

$sheetLayout = @(
    @{ X=900;  Y=1300; W=2800; H=1400; Key='power';     Number='100' },
    @{ X=4400; Y=1300; W=2800; H=1400; Key='teensy';    Number='200' },
    @{ X=7900; Y=1300; W=2800; H=1400; Key='can';       Number='300-500' },
    @{ X=900;  Y=3600; W=2800; H=1400; Key='safety';    Number='600' },
    @{ X=4400; Y=3600; W=2800; H=1400; Key='monitor';   Number='700' },
    @{ X=7900; Y=3600; W=2800; H=1400; Key='expansion'; Number='800-900' }
)
$uid = 0x7000
foreach ($box in $sheetLayout) {
    $uid++
    $d = $definitions[$box.Key]
    $root.Add('$Sheet')
    $root.Add("S $($box.X) $($box.Y) $($box.W) $($box.H)")
    $root.Add("U $($uid.ToString('X'))")
    $root.Add("F0 `"$($box.Number) $($d.Title)`" 60")
    $root.Add("F1 `"modules/$($d.File)`" 50")
    $root.Add('$EndSheet')
}

$root.Add('Text Notes 900 5800 0    55   ~ 12')
$root.Add('Cross-module nets use global labels: +5V_SYS, +5V_TEENSY, +3V3_TEENSY, GND_CTRL, CANx_TX/RX, safety and I2C signals.')
$root.Add('Text Notes 900 6050 0    55   ~ 12')
$root.Add('PCB gate: replace pin-explicit generic IC symbols, close every TBD, save as current .kicad_sch, then reach ERC 0.')
$root.Add('$EndSCHEMATC')
[System.IO.File]::WriteAllLines((Join-Path $projectPath 'central-board.sch'), $root, [System.Text.UTF8Encoding]::new($false))

if ([System.IO.File]::Exists($flatPath)) {
    [System.IO.File]::Delete($flatPath)
}

Write-Host "Generated root and $($definitions.Count) responsibility modules in $projectPath"
