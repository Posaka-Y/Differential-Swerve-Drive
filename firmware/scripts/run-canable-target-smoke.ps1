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

function ConvertTo-I32LeHex {
    param([int]$Value)
    $bytes = [BitConverter]::GetBytes([int32]$Value)
    -join ($bytes | ForEach-Object { $_.ToString("X2") })
}

function Write-Slcan {
    param(
        [System.IO.Ports.SerialPort]$Port,
        [string]$Command,
        [int]$DelayMs = 10
    )
    $Port.WriteLine($Command)
    Start-Sleep -Milliseconds $DelayMs
}

function Read-AvailableLines {
    param([System.IO.Ports.SerialPort]$Port)
    $lines = New-Object System.Collections.Generic.List[string]
    while ($Port.BytesToRead -gt 0) {
        $line = $Port.ReadLine()
        $lines.Add($line.TrimEnd("`r", "`n"))
    }
    $lines
}

$setTargetId = 0x100 + $UnitId
$unitCtrlId = 0x120 + $UnitId
$targetFrame = "t{0:X3}8{1}{2}" -f $setTargetId,
    (ConvertTo-I32LeHex $TargetSteerMdeg),
    (ConvertTo-I32LeHex $WheelRpmMilli)
$enableFrame = "t{0:X3}20101" -f $unitCtrlId
$disableFrame = "t{0:X3}20100" -f $unitCtrlId

$debug = [System.IO.Ports.SerialPort]::new($DebugPort, 115200, [System.IO.Ports.Parity]::None, 8, [System.IO.Ports.StopBits]::One)
$debug.NewLine = "`n"
$debug.ReadTimeout = 50
$debug.Open()
$debug.DiscardInBuffer()

$can = [System.IO.Ports.SerialPort]::new($CanPort, $SerialBaud, [System.IO.Ports.Parity]::None, 8, [System.IO.Ports.StopBits]::One)
$can.NewLine = "`r"
$can.ReadTimeout = 50
$can.Open()
$can.DiscardInBuffer()
$can.DiscardOutBuffer()

$captured = New-Object System.Collections.Generic.List[string]
try {
    Write-Slcan $can "C"
    Write-Slcan $can "S8"
    Write-Slcan $can "O"

    # Put the target on the bus before enabling. The unit must remain idle until
    # UNIT_CTRL enable arrives.
    for ($i = 0; $i -lt 10; $i++) {
        Write-Slcan $can $targetFrame 5
        foreach ($line in (Read-AvailableLines $debug)) { $captured.Add($line) }
        Start-Sleep -Milliseconds 45
    }

    Write-Slcan $can $enableFrame
    $stopAt = [DateTimeOffset]::Now.AddSeconds($RunSeconds)
    while ([DateTimeOffset]::Now -lt $stopAt) {
        Write-Slcan $can $targetFrame 5
        foreach ($line in (Read-AvailableLines $debug)) { $captured.Add($line) }
        Start-Sleep -Milliseconds ([Math]::Max(1, $PeriodMs - 5))
    }
}
finally {
    try { Write-Slcan $can $disableFrame } catch {}
    Start-Sleep -Milliseconds 250
    try {
        foreach ($line in (Read-AvailableLines $debug)) { $captured.Add($line) }
    } catch {}
    if ($can.IsOpen) { $can.Close() }
    if ($debug.IsOpen) { $debug.Close() }
}

[pscustomobject]@{
    CanPort         = $CanPort
    DebugPort       = $DebugPort
    TargetFrame     = $targetFrame
    EnableFrame     = $enableFrame
    DisableFrame    = $disableFrame
    TargetSteerMdeg = $TargetSteerMdeg
    WheelRpmMilli   = $WheelRpmMilli
    RunSeconds      = $RunSeconds
    CapturedLines   = $captured.ToArray()
}
