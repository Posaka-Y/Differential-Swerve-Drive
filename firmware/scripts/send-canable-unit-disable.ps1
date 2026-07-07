[CmdletBinding()]
param(
    [string]$CanPort = "COM16",
    [int]$SerialBaud = 115200,
    [int]$UnitId = 1
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$unitCtrlId = 0x120 + $UnitId
$disableFrame = "t{0:X3}20100" -f $unitCtrlId
$can = [System.IO.Ports.SerialPort]::new($CanPort, $SerialBaud, [System.IO.Ports.Parity]::None, 8, [System.IO.Ports.StopBits]::One)
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
