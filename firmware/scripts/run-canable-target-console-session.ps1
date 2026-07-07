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

$hardwareSession = Join-Path $PSScriptRoot "invoke-hardware-session.ps1"
$console = Join-Path $PSScriptRoot "run-canable-target-console.ps1"
$disable = Join-Path $PSScriptRoot "send-canable-unit-disable.ps1"

& $hardwareSession `
    -Owner "canable-target-console" `
    -Body {
        & $console `
            -CanPort $CanPort `
            -SerialBaud $SerialBaud `
            -UnitId $UnitId `
            -InitialSteerMdeg $InitialSteerMdeg `
            -InitialWheelRpmMilli $InitialWheelRpmMilli `
            -WheelStepRpmMilli $WheelStepRpmMilli `
            -MaxAbsWheelRpmMilli $MaxAbsWheelRpmMilli `
            -SteerStepMdeg $SteerStepMdeg `
            -PeriodMs $PeriodMs
    } `
    -SafeIdle {
        & $disable -CanPort $CanPort -SerialBaud $SerialBaud -UnitId $UnitId
    }
