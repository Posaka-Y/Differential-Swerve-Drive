[CmdletBinding()]
param(
    [string]$CanPort = "COM16",
    [string]$DebugPort = "COM15",
    [int]$SerialBaud = 115200,
    [int]$UnitId = 1,
    [int]$TargetSteerMdeg,
    [int]$WheelRpmMilli = 500000,
    [double]$RunSeconds = 8.0,
    [int]$PeriodMs = 50
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$hardwareSession = Join-Path $PSScriptRoot "invoke-hardware-session.ps1"
$flash = Join-Path $PSScriptRoot "flash.ps1"
$smoke = Join-Path $PSScriptRoot "run-canable-target-smoke.ps1"

function Send-CanableDisable {
    param(
        [string]$PortName,
        [int]$Baud,
        [int]$TargetUnitId
    )

    $unitCtrlId = 0x120 + $TargetUnitId
    $disableFrame = "t{0:X3}20100" -f $unitCtrlId
    $can = [System.IO.Ports.SerialPort]::new($PortName, $Baud, [System.IO.Ports.Parity]::None, 8, [System.IO.Ports.StopBits]::One)
    $can.NewLine = "`r"
    try {
        $can.Open()
        $can.DiscardInBuffer()
        $can.DiscardOutBuffer()
        foreach ($cmd in @("C", "S8", "O", $disableFrame, $disableFrame)) {
            $can.WriteLine($cmd)
            Start-Sleep -Milliseconds 20
        }
    }
    finally {
        if ($can.IsOpen) { $can.Close() }
    }

    $disableFrame
}

& $hardwareSession `
    -Owner "canable-target-smoke" `
    -Body {
        Push-Location $repoRoot
        try {
            & $flash
            Start-Sleep -Milliseconds 750
            & $smoke `
                -CanPort $CanPort `
                -DebugPort $DebugPort `
                -SerialBaud $SerialBaud `
                -UnitId $UnitId `
                -TargetSteerMdeg $TargetSteerMdeg `
                -WheelRpmMilli $WheelRpmMilli `
                -RunSeconds $RunSeconds `
                -PeriodMs $PeriodMs
        }
        finally {
            Pop-Location
        }
    } `
    -SafeIdle {
        Send-CanableDisable -PortName $CanPort -Baud $SerialBaud -TargetUnitId $UnitId
    }
