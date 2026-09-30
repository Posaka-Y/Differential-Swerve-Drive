param(
    [string]$OutputPath = "hardware/central-board/central-board/modules-generated/100-power-rev1.sch"
)

$ErrorActionPreference = "Stop"
$script:lines = [System.Collections.Generic.List[string]]::new()
$script:uid = 0x9000

function Add-Line([string]$Text) {
    $script:lines.Add($Text)
}

function Add-Component {
    param(
        [string]$LibraryId,
        [string]$Reference,
        [string]$Value,
        [int]$X,
        [int]$Y,
        [string]$Orientation = "-1 0 0 1",
        [string]$Footprint = ""
    )
    $script:uid++
    Add-Line '$Comp'
    Add-Line "L $LibraryId $Reference"
    Add-Line "U 1 1 $($script:uid.ToString('X'))"
    Add-Line "P $X $Y"
    Add-Line "F 0 `"$Reference`" H $($X - 100) $($Y + 220) 50  0000 C CNN"
    Add-Line "F 1 `"$Value`" H $($X - 100) $($Y + 130) 50  0000 C CNN"
    Add-Line "F 2 `"$Footprint`" H $X $Y 50  0001 C CNN"
    Add-Line "`t1    $X $Y"
    Add-Line "`t$Orientation"
    Add-Line '$EndComp'
}

function Add-Wire([int]$X1, [int]$Y1, [int]$X2, [int]$Y2) {
    Add-Line 'Wire Wire Line'
    Add-Line "`t$X1 $Y1 $X2 $Y2"
}

function Add-Label([int]$X, [int]$Y, [string]$Name, [int]$Orientation = 0) {
    Add-Line "Text Label $X $Y $Orientation    40   ~ 0"
    Add-Line $Name
}

function Add-Note([int]$X, [int]$Y, [string]$Text, [int]$Size = 60) {
    Add-Line "Text Notes $X $Y 0    $Size   ~ 12"
    Add-Line $Text
}

function Add-ConnectorLabels {
    param(
        [int]$X,
        [int]$Y,
        [string[]]$Nets,
        [int]$Stub = 500
    )
    for ($index = 0; $index -lt $Nets.Count; $index++) {
        $pinY = $Y + 100 * $index
        Add-Wire ($X + 200) $pinY ($X + $Stub) $pinY
        Add-Label ($X + $Stub) $pinY $Nets[$index]
    }
}

function Add-HorizontalPassive {
    param(
        [string]$LibraryId,
        [string]$Reference,
        [string]$Value,
        [int]$X,
        [int]$Y,
        [string]$LeftNet,
        [string]$RightNet,
        [string]$Footprint = ""
    )
    Add-Component $LibraryId $Reference $Value $X $Y "0 -1 -1 0" $Footprint
    Add-Wire ($X - 100) $Y ($X - 350) $Y
    Add-Label ($X - 350) $Y $LeftNet
    Add-Wire ($X + 100) $Y ($X + 350) $Y
    Add-Label ($X + 350) $Y $RightNet
}

Add-Line 'EESchema Schematic File Version 4'
Add-Line 'LIBS:power'
Add-Line 'LIBS:device'
Add-Line 'LIBS:Connector_Generic'
Add-Line 'EELAYER 29 0'
Add-Line 'EELAYER END'
Add-Line '$Descr A3 16535 11693'
Add-Line 'encoding utf-8'
Add-Line 'Sheet 1 1'
Add-Line 'Title "100 Power Input and 5V Distribution - external 5V in, TPS259470 eFuse"'
Add-Line 'Date "2026-09-14"'
Add-Line 'Rev "A - HUMAN REVIEW DRAFT"'
Add-Line 'Comp "Differential Swerve"'
Add-Line 'Comment1 "Pin-explicit generic symbols; replace with real library parts before PCB layout"'
Add-Line 'Comment2 "Source of truth: docs/electrical/CENTRAL_BOARD_REQUIREMENTS.md"'
Add-Line '$EndDescr'

# ---------------------------------------------------------------------------
# 24V input and protection (values TBD per CENTRAL_BOARD_POWER_BLOCK_REV1.md)
# ---------------------------------------------------------------------------
Add-Note 600 700 '100 POWER (5V IN FROM EXTERNAL SD-25B-5 BUCK)' 80
Add-Component 'Connector_Generic:Conn_01x02' 'J101' 'XT30PW-M 5V INPUT' 900 1100 '-1 0 0 1' 'Connector_AMASS:AMASS_XT30PW-M_1x02_P5.00mm_Horizontal'
Add-ConnectorLabels 900 1100 @('+5V_RAW','GND_CTRL')
Add-HorizontalPassive 'Device:Fuse' 'F101' '5A FUSE TBD' 1700 1100 '+5V_RAW' '+5V_FUSED_IN'
Add-HorizontalPassive 'Device:D_TVS' 'D101' 'SMBJ5.0A' 1700 1400 '+5V_FUSED_IN' 'GND_CTRL'

# ---------------------------------------------------------------------------
# TPS259470LRPWR eFuse (pin-explicit placeholder)
# ---------------------------------------------------------------------------
Add-Component 'Connector_Generic:Conn_01x10' 'U101' 'TPS259470LRPWR' 2350 1000 '-1 0 0 1' 'Package_DFN_QFN:WQFN-10-1EP_2x2mm_P0.5mm_EP0.75x1.6mm'
Add-ConnectorLabels 2350 1000 @('EN_UVLO','OVLO','AUXOFF','PWR_5V_FAULT_N','+5V_FUSED_IN','+5V_PROT','DVDT','GND_CTRL','ILM','ITIMER') 750
Add-HorizontalPassive 'Device:R' 'R101' '221k 1%' 3300 1050 '+5V_FUSED_IN' 'OVLO'
Add-HorizontalPassive 'Device:R' 'R102' '732k 1%' 3300 1250 'OVLO' 'EN_UVLO'
Add-HorizontalPassive 'Device:R' 'R103' '51.1k 1%' 3300 1450 'EN_UVLO' 'GND_CTRL'
Add-HorizontalPassive 'Device:R' 'R104' '750R (ILIM)' 3300 1650 'ILM' 'GND_CTRL'
Add-HorizontalPassive 'Device:C' 'C101' 'DVDT TBD' 3300 1850 'DVDT' 'GND_CTRL'
Add-HorizontalPassive 'Device:C' 'C102' 'ITIMER TBD' 3300 2050 'ITIMER' 'GND_CTRL'
Add-HorizontalPassive 'Device:R' 'R105' '10k' 3300 2250 'PWR_5V_FAULT_N' '+3V3_TEENSY'

# ---------------------------------------------------------------------------
# 5V star distribution to module boards + Teensy branch (source: +5V_PROT)
# ---------------------------------------------------------------------------
Add-Note 600 3100 '5V DISTRIBUTION' 80
Add-Component 'Connector_Generic:Conn_01x02' 'J111' 'UNIT1 5V OUT GH2' 850 3550 '-1 0 0 1' 'Connector_JST:JST_GH_SM02B-GHS-TB_1x02-1MP_P1.25mm_Horizontal'
Add-ConnectorLabels 850 3550 @('+5V_UNIT1','GND_CTRL')
Add-HorizontalPassive 'Device:Polyfuse' 'F111' '1206L050/15YR' 1750 3550 '+5V_PROT' '+5V_UNIT1'
Add-Component 'Connector_Generic:Conn_01x02' 'J112' 'UNIT2 5V OUT GH2' 850 3900 '-1 0 0 1' 'Connector_JST:JST_GH_SM02B-GHS-TB_1x02-1MP_P1.25mm_Horizontal'
Add-ConnectorLabels 850 3900 @('+5V_UNIT2','GND_CTRL')
Add-HorizontalPassive 'Device:Polyfuse' 'F112' '1206L050/15YR' 1750 3900 '+5V_PROT' '+5V_UNIT2'
Add-Component 'Connector_Generic:Conn_01x02' 'J113' 'UNIT3 5V OUT GH2' 850 4250 '-1 0 0 1' 'Connector_JST:JST_GH_SM02B-GHS-TB_1x02-1MP_P1.25mm_Horizontal'
Add-ConnectorLabels 850 4250 @('+5V_UNIT3','GND_CTRL')
Add-HorizontalPassive 'Device:Polyfuse' 'F113' '1206L050/15YR' 1750 4250 '+5V_PROT' '+5V_UNIT3'
Add-Component 'Connector_Generic:Conn_01x02' 'J114' 'ODOM 5V OUT GH2' 850 4600 '-1 0 0 1' 'Connector_JST:JST_GH_SM02B-GHS-TB_1x02-1MP_P1.25mm_Horizontal'
Add-ConnectorLabels 850 4600 @('+5V_ODOM','GND_CTRL')
Add-HorizontalPassive 'Device:Polyfuse' 'F114' '1206L050/15YR' 1750 4600 '+5V_PROT' '+5V_ODOM'

Add-HorizontalPassive 'Device:Polyfuse' 'F115' '1206L075/16WR' 3100 3550 '+5V_PROT' '+5V_SYS'
Add-HorizontalPassive 'Device:Polyfuse' 'F116' '1206L050/15YR' 3100 3900 '+5V_PROT' '+5V_EXP'

Add-Component 'Device:LED' 'D111' 'LTST-C190KGKT' 2600 3550 '0 -1 -1 0' 'LED_SMD:LED_0603_1608Metric'
Add-HorizontalPassive 'Device:R' 'R111' '1.5k' 2900 3550 'D111_K' 'GND_CTRL'
Add-Wire 1850 3550 2500 3550
Add-Wire 2700 3550 2800 3550
Add-Label 2800 3550 'D111_K'

# ---------------------------------------------------------------------------
# 150: Teensy power in (VIN diode-OR with USB, per 2026-09-12 confirmed decision)
# ---------------------------------------------------------------------------
Add-Note 5400 3100 '150 TEENSY VIN' 70
Add-Component 'Device:D_Schottky' 'D151' 'SCHOTTKY TBD' 5700 3550 '0 -1 -1 0' ''
Add-Wire 5100 3550 5600 3550
Add-Label 5100 3550 '+5V_SYS'
Add-Wire 5800 3550 6200 3550
Add-Label 6200 3550 'VIN_TEENSY'
Add-Component 'Device:D_Schottky' 'D152' 'SCHOTTKY TBD' 5700 3800 '0 -1 -1 0' ''
Add-Wire 5100 3800 5600 3800
Add-Label 5100 3800 'TEENSY_VUSB_PAD'
Add-Wire 5800 3800 6200 3800
Add-Wire 6200 3800 6200 3550
Add-Note 5450 4050 'Cut Teensy VUSB-VIN jumper before assembly.' 45

Add-Line '$EndSCHEMATC'

$resolvedOutput = if ([System.IO.Path]::IsPathRooted($OutputPath)) {
    $OutputPath
} else {
    Join-Path (Get-Location) $OutputPath
}
$outputDirectory = Split-Path -Parent $resolvedOutput
New-Item -ItemType Directory -Force -Path $outputDirectory | Out-Null
[System.IO.File]::WriteAllLines($resolvedOutput, $script:lines, [System.Text.UTF8Encoding]::new($false))
Write-Host "Generated $resolvedOutput"
