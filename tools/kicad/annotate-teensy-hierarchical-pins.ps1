param(
    [string]$SchematicPath = "hardware/central-board/central-board/modules/200-teensy.kicad_sch"
)

$ErrorActionPreference = "Stop"
$resolved = (Resolve-Path $SchematicPath).Path
$content = [System.IO.File]::ReadAllText($resolved)

# socket pad 1..24 is J1 pin 1..24. socket pad 25..48 is J2 pin 1..24.
# The two symbols are drawn as the actual two Teensy 4.1 socket rows.
$padNets = @(
    'GND_CTRL','CAN2_RX','CAN2_TX','MOTOR_PWR_EN','ESTOP_LOOP_OK_N','ESTOP1_AUX_OK_N',
    'ESTOP2_AUX_OK_N','REARM_SW_N','STATUS_G_LED','STATUS_R_LED','AUX_OUTPUT_EN',
    'SPI_CS0_N','SPI_MOSI','SPI_MISO','+3V3_TEENSY','IO24_A10','IO25_A11','IO26_A12',
    'IO27_A13','UART7_RX','UART7_TX','CAN3_RX','CAN3_TX','PWR_5V_FAULT_N',
    $null,'UART8_RX','UART8_TX','SPI_CS1_N',$null,$null,$null,'IO40_A16','IO41_A17',
    'GND_CTRL','SPI_SCK','MOTOR_PWR_SENSE','BAT_MON_ALERT_N','I2C1_SCL','I2C1_SDA',
    'I2C0_SDA','I2C0_SCL','IO20_A6','IO21_A7','CAN1_TX','CAN1_RX','+3V3_TEENSY',
    'GND_CTRL','+5V_TEENSY'
)

$inputNames = @(
    'CAN1_RX','CAN2_RX','CAN3_RX','ESTOP_LOOP_OK_N','ESTOP1_AUX_OK_N',
    'ESTOP2_AUX_OK_N','REARM_SW_N','SPI_MISO','UART7_RX','UART8_RX',
    'PWR_5V_FAULT_N','MOTOR_PWR_SENSE','BAT_MON_ALERT_N','+5V_TEENSY'
)
$outputNames = @(
    'CAN1_TX','CAN2_TX','CAN3_TX','MOTOR_PWR_EN','AUX_OUTPUT_EN','STATUS_G_LED',
    'STATUS_R_LED','SPI_CS0_N','SPI_CS1_N','SPI_MOSI','SPI_SCK','UART7_TX',
    'UART8_TX','+3V3_TEENSY'
)

function Get-Shape([string]$Name) {
    if ($inputNames -contains $Name) { return 'input' }
    if ($outputNames -contains $Name) { return 'output' }
    return 'bidirectional'
}

# Remove the old detached pin-map wires/labels and any previous NC pass.
$content = [regex]::Replace($content, '(?ms)^\t\(wire\r?\n.*?^\t\)\r?\n', '')
$content = [regex]::Replace($content, '(?ms)^\t\((?:label|hierarchical_label) "[^"]+"\r?\n.*?^\t\)\r?\n', '')
$content = [regex]::Replace($content, '(?ms)^\t\(no_connect\r?\n.*?^\t\)\r?\n', '')

$annotations = [System.Text.StringBuilder]::new()
for ($pad = 1; $pad -le 48; $pad++) {
    if ($pad -le 24) {
        $x = '60.96'
        $y = (39.37 + 2.54 * ($pad - 1)).ToString('0.##', [cultureinfo]::InvariantCulture)
        $angle = '180'
        $justify = 'right bottom'
    } else {
        $x = '97.79'
        $y = (39.37 + 2.54 * ($pad - 25)).ToString('0.##', [cultureinfo]::InvariantCulture)
        $angle = '0'
        $justify = 'left bottom'
    }

    $uuidSuffix = $pad.ToString('000000000000')
    $name = $padNets[$pad - 1]
    if ($null -eq $name) {
        [void]$annotations.Append("`t(no_connect`r`n")
        [void]$annotations.Append("`t`t(at $x $y)`r`n")
        [void]$annotations.Append("`t`t(uuid `"a0000000-0000-4000-8000-$uuidSuffix`")`r`n")
        [void]$annotations.Append("`t)`r`n")
        continue
    }

    $shape = Get-Shape $name
    [void]$annotations.Append("`t(hierarchical_label `"$name`"`r`n")
    [void]$annotations.Append("`t`t(shape $shape)`r`n")
    [void]$annotations.Append("`t`t(at $x $y $angle)`r`n")
    [void]$annotations.Append("`t`t(effects`r`n")
    [void]$annotations.Append("`t`t`t(font`r`n`t`t`t`t(size 1.016 1.016)`r`n`t`t`t)`r`n")
    [void]$annotations.Append("`t`t`t(justify $justify)`r`n")
    [void]$annotations.Append("`t`t)`r`n")
    [void]$annotations.Append("`t`t(uuid `"b0000000-0000-4000-8000-$uuidSuffix`")`r`n")
    [void]$annotations.Append("`t)`r`n")
}

$componentMarker = "`t(symbol`r`n`t`t(lib_id "
$insertAt = $content.IndexOf($componentMarker)
if ($insertAt -lt 0) {
    throw "Could not find top-level component insertion point in $resolved"
}
$content = $content.Insert($insertAt, $annotations.ToString())

[System.IO.File]::WriteAllText($resolved, $content, [System.Text.UTF8Encoding]::new($false))
Write-Host "Attached 44 hierarchical labels and four No Connect flags directly to the Teensy socket pins: $resolved"
