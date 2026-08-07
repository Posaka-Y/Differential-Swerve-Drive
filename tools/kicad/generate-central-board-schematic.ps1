param(
    [string]$OutputPath = "hardware/central-board/central-board.sch"
)

$ErrorActionPreference = "Stop"
$script:lines = [System.Collections.Generic.List[string]]::new()
$script:uid = 0x1000

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
Add-Line 'LIBS:Switch'
Add-Line 'LIBS:Transistor_FET'
Add-Line 'EELAYER 29 0'
Add-Line 'EELAYER END'
Add-Line '$Descr A3 16535 11693'
Add-Line 'encoding utf-8'
Add-Line 'Sheet 1 1'
Add-Line 'Title "Teensy 4.1 Central CAN Master Board"'
Add-Line 'Date "2026-08-04"'
Add-Line 'Rev "A - HUMAN REVIEW DRAFT"'
Add-Line 'Comp "Differential Swerve"'
Add-Line 'Comment1 "Flat schematic; labels are electrical connections"'
Add-Line 'Comment2 "TBD items must be closed before PCB layout"'
Add-Line '$EndDescr'

# ---------------------------------------------------------------------------
# 100: 5 V input, eFuse and branch distribution
# ---------------------------------------------------------------------------
Add-Note 600 700 '100 POWER INPUT / eFUSE / STAR DISTRIBUTION' 80
Add-Component 'Connector_Generic:Conn_01x02' 'J101' 'XT30PW-M 5V INPUT' 900 1100 '-1 0 0 1' 'Connector_AMASS:AMASS_XT30PW-M_1x02_P5.00mm_Horizontal'
Add-ConnectorLabels 900 1100 @('+5V_RAW','GND_CTRL')
Add-HorizontalPassive 'Device:Fuse' 'F101' '5A FUSE / TBD TYPE' 1700 1100 '+5V_RAW' '+5V_FUSED'
Add-HorizontalPassive 'Device:D_TVS' 'D101' 'SMBJ5.0A / VERIFY' 1700 1400 '+5V_FUSED' 'GND_CTRL'
Add-Component 'Connector_Generic:Conn_01x10' 'U101' 'TPS259470LRPWR' 2350 1000 '-1 0 0 1' 'Package_DFN_QFN:WQFN-10-1EP_2x2mm_P0.5mm_EP0.75x1.6mm'
Add-ConnectorLabels 2350 1000 @('EN_UVLO','OVLO','AUXOFF','PWR_5V_FAULT_N','+5V_FUSED','+5V_SYS','DVDT','GND_CTRL','ILM','ITIMER') 750
Add-Note 2250 2050 'U101 pin order 1..10 shown top-to-bottom' 45
Add-HorizontalPassive 'Device:R' 'R101' 'UVLO TOP - TBD TOLERANCE' 3300 1050 '+5V_FUSED' 'EN_UVLO'
Add-HorizontalPassive 'Device:R' 'R102' 'UVLO BOT - TBD' 3300 1250 'EN_UVLO' 'GND_CTRL'
Add-HorizontalPassive 'Device:R' 'R103' 'OVLO TOP - TBD TOLERANCE' 3300 1450 '+5V_FUSED' 'OVLO'
Add-HorizontalPassive 'Device:R' 'R104' 'OVLO BOT - TBD' 3300 1650 'OVLO' 'GND_CTRL'
Add-HorizontalPassive 'Device:R' 'R105' '750R (ILIM INITIAL)' 3300 1850 'ILM' 'GND_CTRL'
Add-HorizontalPassive 'Device:C' 'C101' 'DVDT - TBD' 3300 2050 'DVDT' 'GND_CTRL'
Add-HorizontalPassive 'Device:C' 'C102' 'ITIMER - TBD' 3300 2250 'ITIMER' 'GND_CTRL'
Add-HorizontalPassive 'Device:R' 'R106' '10k' 3300 2450 'PWR_5V_FAULT_N' '+3V3_TEENSY'
Add-Note 650 2650 'CAUTION: OVLO must include rail + comparator + resistor tolerance; nominal 5.45V is too close to Teensy VIN max 5.5V.' 50

Add-Component 'Connector_Generic:Conn_01x02' 'J111' 'UNIT1 5V OUT GH2' 850 3150 '-1 0 0 1' 'Connector_JST:JST_GH_SM02B-GHS-TB_1x02-1MP_P1.25mm_Horizontal'
Add-ConnectorLabels 850 3150 @('+5V_UNIT1','GND_CTRL')
Add-HorizontalPassive 'Device:Polyfuse' 'F111' '1206L050/15YR' 1750 3150 '+5V_SYS' '+5V_UNIT1'
Add-Component 'Connector_Generic:Conn_01x02' 'J112' 'UNIT2 5V OUT GH2' 850 3500 '-1 0 0 1' 'Connector_JST:JST_GH_SM02B-GHS-TB_1x02-1MP_P1.25mm_Horizontal'
Add-ConnectorLabels 850 3500 @('+5V_UNIT2','GND_CTRL')
Add-HorizontalPassive 'Device:Polyfuse' 'F112' '1206L050/15YR' 1750 3500 '+5V_SYS' '+5V_UNIT2'
Add-Component 'Connector_Generic:Conn_01x02' 'J113' 'UNIT3 5V OUT GH2' 850 3850 '-1 0 0 1' 'Connector_JST:JST_GH_SM02B-GHS-TB_1x02-1MP_P1.25mm_Horizontal'
Add-ConnectorLabels 850 3850 @('+5V_UNIT3','GND_CTRL')
Add-HorizontalPassive 'Device:Polyfuse' 'F113' '1206L050/15YR' 1750 3850 '+5V_SYS' '+5V_UNIT3'
Add-Component 'Connector_Generic:Conn_01x02' 'J114' 'ODOM 5V OUT GH2' 850 4200 '-1 0 0 1' 'Connector_JST:JST_GH_SM02B-GHS-TB_1x02-1MP_P1.25mm_Horizontal'
Add-ConnectorLabels 850 4200 @('+5V_ODOM','GND_CTRL')
Add-HorizontalPassive 'Device:Polyfuse' 'F114' '1206L050/15YR' 1750 4200 '+5V_SYS' '+5V_ODOM'
Add-HorizontalPassive 'Device:Polyfuse' 'F115' '1206L075/16YR' 3100 3150 '+5V_SYS' '+5V_TEENSY'
Add-HorizontalPassive 'Device:Polyfuse' 'F116' '1206L050/15YR' 3100 3500 '+5V_SYS' '+5V_EXP'
Add-Note 650 4550 'Each node branch: add green LED + 1.5k after PPTC and a test point during PCB capture.' 45

# ---------------------------------------------------------------------------
# 200: Teensy sockets
# ---------------------------------------------------------------------------
Add-Note 4050 700 '200 TEENSY 4.1 SOCKETS (TOP-VIEW PIN MAP)' 80
Add-Component 'Connector_Generic:Conn_01x24' 'J201' 'TEENSY LEFT / 68000-224HLF + SOCKET' 4200 1050 '-1 0 0 1' 'Connector_PinSocket_2.54mm:PinSocket_1x24_P2.54mm_Vertical'
$leftPins = @('GND_CTRL','CAN2_RX','CAN2_TX','MOTOR_PWR_EN','ESTOP_LOOP_OK_N','ESTOP1_AUX_OK_N','ESTOP2_AUX_OK_N','REARM_SW_N','STATUS_G_LED','STATUS_R_LED','AUX_OUTPUT_EN','SPI_CS0_N','SPI_MOSI','SPI_MISO','+3V3_TEENSY','IO24_A10','IO25_A11','IO26_A12','IO27_A13','UART7_RX','UART7_TX','CAN3_RX','CAN3_TX','PWR_5V_FAULT_N')
Add-ConnectorLabels 4200 1050 $leftPins 1050
Add-Component 'Connector_Generic:Conn_01x24' 'J202' 'TEENSY RIGHT / 68000-224HLF + SOCKET' 5550 1050 '-1 0 0 1' 'Connector_PinSocket_2.54mm:PinSocket_1x24_P2.54mm_Vertical'
$rightPins = @('TP_GPIO33','UART8_RX','UART8_TX','SPI_CS1_N','TP_GPIO37','TP_GPIO38','TP_GPIO39','IO40_A16','IO41_A17','GND_CTRL','SPI_SCK','MOTOR_PWR_SENSE','BAT_MON_ALERT_N','I2C1_SCL','I2C1_SDA','I2C0_SDA','I2C0_SCL','IO20_A6','IO21_A7','CAN1_TX','CAN1_RX','+3V3_TEENSY','GND_CTRL','+5V_TEENSY')
Add-ConnectorLabels 5550 1050 $rightPins 1050
Add-Note 4050 3600 'J201 socket pads 1..24 = Teensy GND,0..12,3V3,24..32.' 45
Add-Note 4050 3700 'J202 socket pads 25..48 = Teensy 33..41,GND,13..23,3V3,GND,VIN.' 45
Add-Note 4050 3800 'MECHANICAL: two 1x24 sockets, 17.78mm row spacing; keep entire underside free of parts/exposed pads.' 50
Add-Note 4050 3910 'ASSEMBLY: cut Teensy VUSB-VIN link before simultaneous external 5V and USB connection.' 50
Add-HorizontalPassive 'Device:R' 'R201' '47k' 4700 4200 'MOTOR_PWR_EN' 'GND_CTRL'
Add-HorizontalPassive 'Device:R' 'R202' '47k' 4700 4400 'AUX_OUTPUT_EN' 'GND_CTRL'
Add-HorizontalPassive 'Device:R' 'R203' '10k' 6000 4200 'REARM_SW_N' '+3V3_TEENSY'
Add-Component 'Switch:SW_Push' 'SW201' 'REARM (BOARD LOCAL OPTION)' 6000 4500 '0 -1 -1 0' 'Button_Switch_THT:SW_PUSH_6mm'
Add-Wire 5900 4500 5650 4500
Add-Label 5650 4500 'REARM_SW_N'
Add-Wire 6100 4500 6350 4500
Add-Label 6120 4500 'GND_CTRL'
Add-Note 4050 4700 'REARM location is open: populate SW201 only if board-local operation is accepted; otherwise use panel connector.' 45

# ---------------------------------------------------------------------------
# 300/400/500: three CAN channels
# ---------------------------------------------------------------------------
function Add-CanBlock {
    param([int]$BaseX,[int]$BaseY,[int]$Hundreds,[string]$Can,[string]$Use,[bool]$Dnp)
    $u = "U$($Hundreds + 1)"; $d = "D$($Hundreds + 1)"; $r = "R$($Hundreds + 1)"; $sw = "SW$($Hundreds + 1)"
    $j1 = "J$($Hundreds + 1)"; $j2 = "J$($Hundreds + 2)"
    $dnpText = if ($Dnp) { ' / DNP DEFAULT' } else { '' }
    Add-Note $BaseX ($BaseY - 300) "$Hundreds $Can - $Use$dnpText" 65
    Add-Component 'Connector_Generic:Conn_01x08' $u 'TCAN1051VDRQ1' ($BaseX + 200) $BaseY '-1 0 0 1' 'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm'
    Add-ConnectorLabels ($BaseX + 200) $BaseY @("${Can}_TX",'GND_CTRL',"+5V_${Can}","${Can}_RX",'+3V3_TEENSY',"${Can}_L","${Can}_H",'GND_CTRL') 700
    Add-Note $BaseX ($BaseY + 900) 'U pin order: TXD,GND,VCC,RXD,VIO,CANL,CANH,S; S tied low.' 40
    Add-HorizontalPassive 'Device:C' "C$($Hundreds + 1)" '100n' ($BaseX + 1250) ($BaseY + 50) "+5V_${Can}" 'GND_CTRL'
    Add-HorizontalPassive 'Device:C' "C$($Hundreds + 2)" '100n' ($BaseX + 1250) ($BaseY + 250) '+3V3_TEENSY' 'GND_CTRL'
    Add-Component 'Connector_Generic:Conn_01x03' $d 'ESD2CAN24DBZRQ1' ($BaseX + 200) ($BaseY + 1250) '-1 0 0 1' 'Package_TO_SOT_SMD:SOT-23'
    Add-ConnectorLabels ($BaseX + 200) ($BaseY + 1250) @("${Can}_H","${Can}_L",'GND_CTRL') 650
    Add-Component 'Connector_Generic:Conn_01x03' $j1 "$Can BUS A GH3" ($BaseX + 200) ($BaseY + 1700) '-1 0 0 1' 'Connector_JST:JST_GH_SM03B-GHS-TB_1x03-1MP_P1.25mm_Horizontal'
    Add-ConnectorLabels ($BaseX + 200) ($BaseY + 1700) @("${Can}_H","${Can}_L",'GND_CTRL') 650
    Add-Component 'Connector_Generic:Conn_01x03' $j2 "$Can BUS B GH3" ($BaseX + 1200) ($BaseY + 1700) '-1 0 0 1' 'Connector_JST:JST_GH_SM03B-GHS-TB_1x03-1MP_P1.25mm_Horizontal'
    Add-ConnectorLabels ($BaseX + 1200) ($BaseY + 1700) @("${Can}_H","${Can}_L",'GND_CTRL') 650
    Add-HorizontalPassive 'Device:R' $r '120R 1%' ($BaseX + 500) ($BaseY + 2200) "${Can}_H" "${Can}_TERM"
    Add-Component 'Switch:SW_SPST' $sw 'TERM ON/OFF' ($BaseX + 1100) ($BaseY + 2200) '0 -1 -1 0' 'Button_Switch_SMD:SW_SPST_CK_JS102011SAQN'
    Add-Wire ($BaseX + 1000) ($BaseY + 2200) ($BaseX + 850) ($BaseY + 2200)
    Add-Label ($BaseX + 850) ($BaseY + 2200) "${Can}_TERM"
    Add-Wire ($BaseX + 1200) ($BaseY + 2200) ($BaseX + 1450) ($BaseY + 2200)
    Add-Label ($BaseX + 1220) ($BaseY + 2200) "${Can}_L"
}
Add-CanBlock 6900 1100 300 'CAN1' 'SENSOR CLASSIC 1Mbps' $false
Add-CanBlock 9950 1100 400 'CAN2' 'EXPANSION / DEBUG' $true
Add-CanBlock 13000 1100 500 'CAN3' 'DRIVE CAN-FD 1M/2M' $false
Add-Note 6900 3850 'All CAN connectors: pin1 COMM_A=CANH, pin2 COMM_B=CANL, pin3 GND. Silkscreen both abstract and physical names.' 45

# ---------------------------------------------------------------------------
# 600: E-stop, contactor and 24 V sensing
# ---------------------------------------------------------------------------
Add-Note 600 5350 '600 E-STOP / CONTACTOR (HARDWARE PATH + ISOLATED MONITOR)' 80
Add-Component 'Connector_Generic:Conn_01x02' 'J601' '24V_CTRL INPUT' 850 5750 '-1 0 0 1' 'Connector_Molex:Molex_Micro-Fit_3.0_43650-0200_1x02_P3.00mm_Horizontal'
Add-ConnectorLabels 850 5750 @('+24V_CTRL_RAW','GND_24V')
Add-HorizontalPassive 'Device:Fuse' 'F601' 'LOOP FUSE TBD' 1750 5750 '+24V_CTRL_RAW' '+24V_LOOP'
Add-HorizontalPassive 'Device:Fuse' 'F602' 'LED/AUX FUSE TBD' 1750 6050 '+24V_CTRL_RAW' '+24V_LED'
Add-HorizontalPassive 'Device:D_TVS' 'D601' '24V TVS TBD' 1750 6350 '+24V_CTRL_RAW' 'GND_24V'
Add-Note 650 6600 'Add 60V-class reverse-polarity/surge protection; exact device TBD after 24V source transient definition.' 45

Add-Component 'Connector_Generic:Conn_01x06' 'J602' 'ESTOP_CTRL 43650-0600' 2700 5700 '-1 0 0 1' 'Connector_Molex:Molex_Micro-Fit_3.0_43650-0600_1x06_P3.00mm_Horizontal'
Add-ConnectorLabels 2700 5700 @('ESTOP_LOOP_OUT','ESTOP_LOOP_RETURN','ESTOP_LED_24V','GND_24V','ESTOP1_AUX_RETURN','ESTOP2_AUX_RETURN') 950
Add-Note 2600 6450 'MATE: Molex 43645-0600 (single-row). 43025-0600 does NOT mate.' 45
Add-HorizontalPassive 'Device:R' 'R601' '0R / LINK' 4100 5700 '+24V_LOOP' 'ESTOP_LOOP_OUT'
Add-HorizontalPassive 'Device:R' 'R602' '0R / LINK' 4100 5900 '+24V_LED' 'ESTOP_LED_24V'

Add-Component 'Connector_Generic:Conn_01x02' 'J603' 'E228 CONTACTOR COIL' 5000 5750 '-1 0 0 1' 'Connector_Molex:Molex_Micro-Fit_3.0_43650-0200_1x02_P3.00mm_Horizontal'
Add-ConnectorLabels 5000 5750 @('ESTOP_LOOP_RETURN','CONTACTOR_COIL_N') 900
Add-Component 'Connector_Generic:Conn_01x03' 'Q601' 'IRLML0100TRPBF PIN-EXPLICIT G/S/D' 5950 5950 '-1 0 0 1' 'Package_TO_SOT_SMD:SOT-23'
Add-ConnectorLabels 5950 5950 @('CONTACTOR_GATE','GND_24V','CONTACTOR_COIL_N') 950
Add-HorizontalPassive 'Device:R' 'R603' '100R' 5200 6250 'MOTOR_PWR_EN' 'CONTACTOR_GATE'
Add-HorizontalPassive 'Device:R' 'R604' '47k' 5700 6500 'CONTACTOR_GATE' 'GND_24V'
Add-HorizontalPassive 'Device:D' 'D602' 'FAST DIODE TBD' 4850 6650 'CONTACTOR_COIL_N' 'ESTOP_LOOP_RETURN'
Add-HorizontalPassive 'Device:D_TVS' 'D603' 'TVS TBD FOR RELEASE TIME' 5750 6800 'CONTACTOR_COIL_N' 'ESTOP_LOOP_RETURN'
Add-Note 4050 7000 'Use diode+TVS clamp as first candidate; verify coil release time and Q601 VDS on oscilloscope. 1N4007-only clamp is not accepted by default.' 45

# Optocoupler input chains are drawn as pin-explicit connector symbols so the shared LTV-847S package can be reviewed.
Add-Component 'Connector_Generic:Conn_01x16' 'U601' 'LTV-847S (PIN-EXPLICIT)' 850 7350 '-1 0 0 1' 'Package_SO:SOP-16_4.4x10.4mm_P1.27mm'
Add-ConnectorLabels 850 7350 @('OPTO1_A','OPTO1_K','OPTO2_A','OPTO2_K','OPTO3_A','OPTO3_K','OPTO4_A','OPTO4_K','OPTO4_E','OPTO4_C','OPTO3_E','OPTO3_C','OPTO2_E','OPTO2_C','OPTO1_E','OPTO1_C') 900
Add-Note 650 9100 'U601 pin order follows LTV-847S datasheet; CH4 spare. Each external 24V input uses two series resistors.' 45
Add-HorizontalPassive 'Device:R' 'R611' '2.2k' 2300 7400 'ESTOP_LOOP_RETURN' 'LOOP_R_MID'
Add-HorizontalPassive 'Device:R' 'R612' '2.2k' 3000 7400 'LOOP_R_MID' 'OPTO1_A'
Add-HorizontalPassive 'Device:R' 'R623' '0R' 2150 7600 'OPTO1_K' 'GND_24V'
Add-HorizontalPassive 'Device:R' 'R613' '2.2k' 2300 7800 'ESTOP1_AUX_RETURN' 'AUX1_R_MID'
Add-HorizontalPassive 'Device:R' 'R614' '2.2k' 3000 7800 'AUX1_R_MID' 'OPTO2_A'
Add-HorizontalPassive 'Device:R' 'R624' '0R' 2150 8000 'OPTO2_K' 'GND_24V'
Add-HorizontalPassive 'Device:R' 'R615' '2.2k' 2300 8200 'ESTOP2_AUX_RETURN' 'AUX2_R_MID'
Add-HorizontalPassive 'Device:R' 'R616' '2.2k' 3000 8200 'AUX2_R_MID' 'OPTO3_A'
Add-HorizontalPassive 'Device:R' 'R625' '0R' 2150 8400 'OPTO3_K' 'GND_24V'
Add-HorizontalPassive 'Device:R' 'R617' '10k' 4000 7450 'OPTO1_C' '+3V3_TEENSY'
Add-HorizontalPassive 'Device:R' 'R618' '10k' 4000 7850 'OPTO2_C' '+3V3_TEENSY'
Add-HorizontalPassive 'Device:R' 'R619' '10k' 4000 8250 'OPTO3_C' '+3V3_TEENSY'
Add-HorizontalPassive 'Device:R' 'R620' '0R' 4700 7450 'OPTO1_C' 'ESTOP_LOOP_OK_N'
Add-HorizontalPassive 'Device:R' 'R621' '0R' 4700 7850 'OPTO2_C' 'ESTOP1_AUX_OK_N'
Add-HorizontalPassive 'Device:R' 'R622' '0R' 4700 8250 'OPTO3_C' 'ESTOP2_AUX_OK_N'
Add-HorizontalPassive 'Device:R' 'R626' '0R' 4000 8550 'OPTO1_E' 'GND_CTRL'
Add-HorizontalPassive 'Device:R' 'R627' '0R' 4700 8650 'OPTO2_E' 'GND_CTRL'
Add-HorizontalPassive 'Device:R' 'R628' '0R' 5400 8750 'OPTO3_E' 'GND_CTRL'
Add-Note 650 9350 '2.2k+2.2k gives about 5mA at 24V, matching the LTV-847S minimum-CTR test condition. Check resistor dissipation and input range.' 45

Add-Component 'Connector_Generic:Conn_01x02' 'J604' 'MOTOR BUS SENSE' 850 9750 '-1 0 0 1' 'Connector_JST:JST_GH_SM02B-GHS-TB_1x02-1MP_P1.25mm_Horizontal'
Add-ConnectorLabels 850 9750 @('MOTOR_BUS_24V','GND_24V')
Add-HorizontalPassive 'Device:R' 'R631' '100k' 2000 9750 'MOTOR_BUS_24V' 'SENSE_DIV'
Add-HorizontalPassive 'Device:R' 'R632' '20k' 2700 10050 'SENSE_DIV' 'GND_CTRL'
Add-HorizontalPassive 'Device:R' 'R633' '1k' 3400 9750 'SENSE_DIV' 'MOTOR_PWR_SENSE'
Add-HorizontalPassive 'Device:C' 'C631' '10n' 4100 10050 'MOTOR_PWR_SENSE' 'GND_CTRL'
Add-Note 650 10350 'Ground-domain assumption: GND_24V and GND_CTRL join at protected control-power entry. Verify before layout.' 45

# ---------------------------------------------------------------------------
# 700: battery monitor
# ---------------------------------------------------------------------------
Add-Note 6500 5350 '700 BATTERY MONITOR (EXTERNAL KELVIN SHUNT)' 80
Add-Component 'Connector_Generic:Conn_01x02' 'J701' 'SHUNT KELVIN INPUT' 6700 5750 '-1 0 0 1' 'Connector_JST:JST_GH_SM02B-GHS-TB_1x02-1MP_P1.25mm_Horizontal'
Add-ConnectorLabels 6700 5750 @('SHUNT_BAT','SHUNT_LOAD') 800
Add-Component 'Connector_Generic:Conn_01x10' 'U701' 'INA238AIDGSR' 7700 5650 '-1 0 0 1' 'Package_SO:VSSOP-10_3x3mm_P0.5mm'
Add-ConnectorLabels 7700 5650 @('GND_CTRL','GND_CTRL','BAT_MON_ALERT_N','I2C0_SDA','I2C0_SCL','+3V3_TEENSY','GND_CTRL','BAT_VBUS','SHUNT_LOAD','SHUNT_BAT') 850
Add-Note 7600 6800 'U701 pin order 1..10: A1,A0,ALERT,SDA,SCL,VS,GND,VBUS,IN-,IN+.' 40
Add-HorizontalPassive 'Device:R' 'R701' '1k' 8850 6000 'SHUNT_LOAD' 'BAT_VBUS'
Add-HorizontalPassive 'Device:C' 'C701' '100n' 8850 6250 '+3V3_TEENSY' 'GND_CTRL'
Add-HorizontalPassive 'Device:R' 'R702' '10k' 8850 6500 'BAT_MON_ALERT_N' '+3V3_TEENSY'
Add-Note 6500 7100 'MANDATORY: fusible resistors/small fuses at the battery-side origins of BOTH Kelvin sense wires; board-side resistors cannot protect the harness.' 45
Add-Note 6500 7220 '100A/75mV shunt dissipates 5.17W at 83A. Confirm continuous/peak current and thermal mounting before purchase.' 45

# ---------------------------------------------------------------------------
# 800/900: expansion and test connectors
# ---------------------------------------------------------------------------
Add-Note 9800 5350 '800 EXPANSION / 900 TEST ACCESS' 80
Add-Component 'Connector_Generic:Conn_01x04' 'J801' 'I2C0 GH4' 9900 5700 '-1 0 0 1' 'Connector_JST:JST_GH_SM04B-GHS-TB_1x04-1MP_P1.25mm_Horizontal'
Add-ConnectorLabels 9900 5700 @('+3V3_TEENSY','GND_CTRL','I2C0_SDA','I2C0_SCL') 800
Add-Component 'Connector_Generic:Conn_01x04' 'J802' 'I2C1 GH4' 9900 6250 '-1 0 0 1' 'Connector_JST:JST_GH_SM04B-GHS-TB_1x04-1MP_P1.25mm_Horizontal'
Add-ConnectorLabels 9900 6250 @('+3V3_TEENSY','GND_CTRL','I2C1_SDA','I2C1_SCL') 800
Add-HorizontalPassive 'Device:R' 'R801' '2.2k DNP' 11300 5750 'I2C0_SDA' '+3V3_TEENSY'
Add-HorizontalPassive 'Device:R' 'R802' '2.2k DNP' 11300 5950 'I2C0_SCL' '+3V3_TEENSY'
Add-HorizontalPassive 'Device:R' 'R803' '2.2k DNP' 11300 6300 'I2C1_SDA' '+3V3_TEENSY'
Add-HorizontalPassive 'Device:R' 'R804' '2.2k DNP' 11300 6500 'I2C1_SCL' '+3V3_TEENSY'

Add-Component 'Connector_Generic:Conn_01x03' 'J811' 'UART7 GH3' 9900 6900 '-1 0 0 1' 'Connector_JST:JST_GH_SM03B-GHS-TB_1x03-1MP_P1.25mm_Horizontal'
Add-ConnectorLabels 9900 6900 @('UART7_TX','UART7_RX','GND_CTRL') 800
Add-Component 'Connector_Generic:Conn_01x03' 'J812' 'UART8 GH3' 9900 7350 '-1 0 0 1' 'Connector_JST:JST_GH_SM03B-GHS-TB_1x03-1MP_P1.25mm_Horizontal'
Add-ConnectorLabels 9900 7350 @('UART8_TX','UART8_RX','GND_CTRL') 800
Add-Component 'Connector_Generic:Conn_01x07' 'J821' 'SPI GH7' 9900 7800 '-1 0 0 1' 'Connector_JST:JST_GH_SM07B-GHS-TB_1x07-1MP_P1.25mm_Horizontal'
Add-ConnectorLabels 9900 7800 @('+3V3_TEENSY','GND_CTRL','SPI_SCK','SPI_MOSI','SPI_MISO','SPI_CS0_N','SPI_CS1_N') 800

Add-Component 'Connector_Generic:Conn_01x10' 'J831' 'GPIO/ADC GH10 - 3V3 ONLY' 12400 5700 '-1 0 0 1' 'Connector_JST:JST_GH_SM10B-GHS-TB_1x10-1MP_P1.25mm_Horizontal'
Add-ConnectorLabels 12400 5700 @('GND_CTRL','+3V3_TEENSY','IO20_A6','IO21_A7','IO24_A10','IO25_A11','IO26_A12','IO27_A13','IO40_A16','IO41_A17') 900
Add-Note 12300 6850 'Add 100R series resistor in each of the eight GPIO lines near Teensy.' 45
Add-Component 'Connector_Generic:Conn_01x03' 'J841' 'AUX DRIVER ENABLE' 12400 7200 '-1 0 0 1' 'Connector_JST:JST_GH_SM03B-GHS-TB_1x03-1MP_P1.25mm_Horizontal'
Add-ConnectorLabels 12400 7200 @('AUX_OUTPUT_EN','+3V3_TEENSY','GND_CTRL') 900
Add-Component 'Connector_Generic:Conn_01x02' 'J842' 'EXTERNAL REARM SW' 12400 7650 '-1 0 0 1' 'Connector_JST:JST_GH_SM02B-GHS-TB_1x02-1MP_P1.25mm_Horizontal'
Add-ConnectorLabels 12400 7650 @('REARM_SW_N','GND_CTRL') 900
Add-Component 'Connector_Generic:Conn_01x06' 'J851' '5V EXPANSION POWER' 12400 8050 '-1 0 0 1' 'Connector_JST:JST_GH_SM06B-GHS-TB_1x06-1MP_P1.25mm_Horizontal'
Add-ConnectorLabels 12400 8050 @('+5V_EXP','GND_CTRL','+3V3_TEENSY','GND_CTRL','NC','NC') 900

Add-Component 'Connector_Generic:Conn_01x08' 'J901' 'TEST POINT HEADER' 14700 5700 '-1 0 0 1' 'Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical'
Add-ConnectorLabels 14700 5700 @('GND_CTRL','+5V_SYS','+3V3_TEENSY','TP_GPIO33','TP_GPIO37','TP_GPIO38','TP_GPIO39','PWR_5V_FAULT_N') 850
Add-Note 9800 9000 'REVIEW GATES BEFORE PCB:' 60
Add-Note 9800 9150 '1) close all TBD ratings/values; 2) confirm rearm location; 3) check eFuse thresholds worst-case;' 45
Add-Note 9800 9270 '4) verify E-stop coil release waveform; 5) confirm source-end shunt fuses; 6) ERC pin-type cleanup after symbol finalization.' 45
Add-Note 9800 9500 'Teensy underside keepout, USB/microSD/Program access and 11mm-class stacking clearance are PCB constraints.' 45
Add-Note 9800 9750 'Net naming: COMM_A/B are harness abstraction; CANH/CANL are physical transceiver nets.' 45
Add-Note 9800 10000 'THIS IS A REVIEW DRAFT. Generic pin-explicit symbols are intentional where final custom library symbols are not yet frozen.' 50

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
