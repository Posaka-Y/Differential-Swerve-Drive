[CmdletBinding()]
param(
    [string]$CanPort = "COM16",
    [int]$SerialBaud = 115200,
    [int]$UnitId = 1,
    [int]$InitialSteerMdeg = 0,
    [int]$InitialWheelRpmMilli = 0,
    [int]$WheelStepRpmMilli = 25000,
    [int]$MaxAbsWheelRpmMilli = 1200000,
    [int]$SteerStepMdeg = 5000,
    [int]$PeriodMs = 50
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function ConvertTo-I32LeHex {
    param([int]$Value)
    $bytes = [BitConverter]::GetBytes([int32]$Value)
    -join ($bytes | ForEach-Object { $_.ToString("X2") })
}

function New-SetTargetFrame {
    param(
        [int]$TargetUnitId,
        [int]$SteerMdeg,
        [int]$WheelRpmMilli
    )

    $setTargetId = 0x100 + $TargetUnitId
    "t{0:X3}8{1}{2}" -f $setTargetId,
        (ConvertTo-I32LeHex $SteerMdeg),
        (ConvertTo-I32LeHex $WheelRpmMilli)
}

function New-UnitCtrlFrame {
    param(
        [int]$TargetUnitId,
        [bool]$Enable
    )

    $unitCtrlId = 0x120 + $TargetUnitId
    $enableByte = if ($Enable) { "01" } else { "00" }
    "t{0:X3}201{1}" -f $unitCtrlId, $enableByte
}

function Write-Slcan {
    param(
        [System.IO.Ports.SerialPort]$Port,
        [string]$Command
    )
    $Port.WriteLine($Command)
}

function Write-Status {
    param(
        [bool]$Enabled,
        [int]$SteerMdeg,
        [int]$WheelRpmMilli
    )

    $steerDeg = $SteerMdeg / 1000.0
    $wheelRpm = $WheelRpmMilli / 1000.0
    $state = if ($Enabled) { "ENABLED" } else { "disabled" }
    Write-Host ("state={0}  theta={1,8:F3} deg  wheel={2,8:F3} rpm" -f $state, $steerDeg, $wheelRpm)
}

function Limit-WheelRpmMilli {
    param([int]$Value)
    if ($Value -gt $MaxAbsWheelRpmMilli) { return $MaxAbsWheelRpmMilli }
    if ($Value -lt -$MaxAbsWheelRpmMilli) { return -$MaxAbsWheelRpmMilli }
    $Value
}

$can = [System.IO.Ports.SerialPort]::new($CanPort, $SerialBaud, [System.IO.Ports.Parity]::None, 8, [System.IO.Ports.StopBits]::One)
$can.NewLine = "`r"
$enabled = $false
$steerMdeg = $InitialSteerMdeg
$wheelRpmMilli = Limit-WheelRpmMilli $InitialWheelRpmMilli
$lastStatus = [DateTimeOffset]::MinValue

Write-Host "CANable target console"
Write-Host "keys: e enable, d disable, q quit"
Write-Host "      up/down wheel +/- step, left/right steer +/- step"
Write-Host "      z/x steer +/- 90deg, 0 wheel=0, h print status"
Write-Host ("steps: wheel={0:F3}rpm steer={1:F3}deg period={2}ms maxWheel=+/-{3:F3}rpm" -f ($WheelStepRpmMilli / 1000.0), ($SteerStepMdeg / 1000.0), $PeriodMs, ($MaxAbsWheelRpmMilli / 1000.0))

try {
    $can.Open()
    $can.DiscardInBuffer()
    $can.DiscardOutBuffer()
    foreach ($cmd in @("C", "S8", "O")) {
        Write-Slcan $can $cmd
        Start-Sleep -Milliseconds 20
    }

    $disableFrame = New-UnitCtrlFrame -TargetUnitId $UnitId -Enable $false
    Write-Slcan $can $disableFrame
    Write-Status -Enabled $enabled -SteerMdeg $steerMdeg -WheelRpmMilli $wheelRpmMilli

    while ($true) {
        while ([Console]::KeyAvailable) {
            $key = [Console]::ReadKey($true)
            switch ($key.Key) {
                "E" {
                    $enabled = $true
                    Write-Slcan $can (New-UnitCtrlFrame -TargetUnitId $UnitId -Enable $true)
                    Write-Status -Enabled $enabled -SteerMdeg $steerMdeg -WheelRpmMilli $wheelRpmMilli
                }
                "D" {
                    $enabled = $false
                    Write-Slcan $can (New-UnitCtrlFrame -TargetUnitId $UnitId -Enable $false)
                    Write-Status -Enabled $enabled -SteerMdeg $steerMdeg -WheelRpmMilli $wheelRpmMilli
                }
                "Q" {
                    return
                }
                "UpArrow" {
                    $wheelRpmMilli = Limit-WheelRpmMilli ($wheelRpmMilli + $WheelStepRpmMilli)
                    Write-Status -Enabled $enabled -SteerMdeg $steerMdeg -WheelRpmMilli $wheelRpmMilli
                }
                "DownArrow" {
                    $wheelRpmMilli = Limit-WheelRpmMilli ($wheelRpmMilli - $WheelStepRpmMilli)
                    Write-Status -Enabled $enabled -SteerMdeg $steerMdeg -WheelRpmMilli $wheelRpmMilli
                }
                "LeftArrow" {
                    $steerMdeg -= $SteerStepMdeg
                    Write-Status -Enabled $enabled -SteerMdeg $steerMdeg -WheelRpmMilli $wheelRpmMilli
                }
                "RightArrow" {
                    $steerMdeg += $SteerStepMdeg
                    Write-Status -Enabled $enabled -SteerMdeg $steerMdeg -WheelRpmMilli $wheelRpmMilli
                }
                "Z" {
                    $steerMdeg -= 90000
                    Write-Status -Enabled $enabled -SteerMdeg $steerMdeg -WheelRpmMilli $wheelRpmMilli
                }
                "X" {
                    $steerMdeg += 90000
                    Write-Status -Enabled $enabled -SteerMdeg $steerMdeg -WheelRpmMilli $wheelRpmMilli
                }
                "D0" {
                    $wheelRpmMilli = 0
                    Write-Status -Enabled $enabled -SteerMdeg $steerMdeg -WheelRpmMilli $wheelRpmMilli
                }
                "NumPad0" {
                    $wheelRpmMilli = 0
                    Write-Status -Enabled $enabled -SteerMdeg $steerMdeg -WheelRpmMilli $wheelRpmMilli
                }
                "H" {
                    Write-Status -Enabled $enabled -SteerMdeg $steerMdeg -WheelRpmMilli $wheelRpmMilli
                }
            }
        }

        Write-Slcan $can (New-SetTargetFrame -TargetUnitId $UnitId -SteerMdeg $steerMdeg -WheelRpmMilli $wheelRpmMilli)
        if (([DateTimeOffset]::Now - $lastStatus).TotalSeconds -ge 2.0) {
            $lastStatus = [DateTimeOffset]::Now
            Write-Status -Enabled $enabled -SteerMdeg $steerMdeg -WheelRpmMilli $wheelRpmMilli
        }
        Start-Sleep -Milliseconds $PeriodMs
    }
}
finally {
    try {
        if ($can.IsOpen) {
            Write-Slcan $can (New-UnitCtrlFrame -TargetUnitId $UnitId -Enable $false)
            Start-Sleep -Milliseconds 20
            Write-Slcan $can (New-UnitCtrlFrame -TargetUnitId $UnitId -Enable $false)
        }
    }
    catch {
    }
    if ($can.IsOpen) { $can.Close() }
    Write-Host "disabled and closed"
}
