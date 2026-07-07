[CmdletBinding()]
param(
    [string]$Port = "COM15",
    [ValidateRange(1200, 3000000)]
    [int]$BaudRate = 115200,
    [ValidateRange(1, 3600)]
    [int]$DurationSeconds = 30,
    [Parameter(Mandatory = $true)]
    [string]$LogFile
)

$ErrorActionPreference = "Stop"

function Get-Stats {
    param([double[]]$Values)

    if ($Values.Count -eq 0) {
        return $null
    }

    $measure = $Values | Measure-Object -Minimum -Maximum -Average
    return [pscustomobject]@{
        Min  = [double]$measure.Minimum
        Max  = [double]$measure.Maximum
        Mean = [double]$measure.Average
    }
}

$logPath = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($LogFile)
$logDirectory = [System.IO.Path]::GetDirectoryName($logPath)
if (-not [System.IO.Directory]::Exists($logDirectory)) {
    throw "Log directory does not exist: $logDirectory"
}

$serial = [System.IO.Ports.SerialPort]::new(
    $Port,
    $BaudRate,
    [System.IO.Ports.Parity]::None,
    8,
    [System.IO.Ports.StopBits]::One
)
$serial.Handshake = [System.IO.Ports.Handshake]::None
$serial.DtrEnable = $false
$serial.RtsEnable = $false
$serial.ReadTimeout = 100

$capture = [System.Text.StringBuilder]::new()
$timer = [System.Diagnostics.Stopwatch]::StartNew()

Write-Host ("Capturing {0} at {1} baud for at most {2}s..." -f `
    $Port, $BaudRate, $DurationSeconds)

try {
    $serial.Open()
    while ($timer.Elapsed.TotalSeconds -lt $DurationSeconds) {
        $text = $serial.ReadExisting()
        if ($text.Length -gt 0) {
            [void]$capture.Append($text)
            if ($capture.ToString() -match '(?m)^\s*STOP:') {
                Start-Sleep -Milliseconds 100
                $tail = $serial.ReadExisting()
                if ($tail.Length -gt 0) {
                    [void]$capture.Append($tail)
                }
                break
            }
        }
        Start-Sleep -Milliseconds 20
    }
}
finally {
    if ($serial.IsOpen) {
        $serial.Close()
    }
    $serial.Dispose()
    $timer.Stop()
}

$lines = @($capture.ToString() -split "`r?`n")
$startIndex = -1
for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match '^\s*START:') {
        $startIndex = $i
    }
}

if ($startIndex -lt 0) {
    throw "No START: line was captured; no log file was written."
}

$stopIndex = -1
for ($i = $startIndex + 1; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match '^\s*STOP:') {
        $stopIndex = $i
        break
    }
}

$endIndex = if ($stopIndex -ge 0) { $stopIndex } else { $lines.Count - 1 }
$segment = @($lines[$startIndex..$endIndex])
while (($segment.Count -gt 0) -and [string]::IsNullOrWhiteSpace($segment[-1])) {
    if ($segment.Count -eq 1) {
        $segment = @()
    }
    else {
        $segment = @($segment[0..($segment.Count - 2)])
    }
}

[System.IO.File]::WriteAllLines(
    $logPath,
    [string[]]$segment,
    [System.Text.UTF8Encoding]::new($false)
)

$samples = [System.Collections.Generic.List[object]]::new()
foreach ($line in $segment) {
    if ($line -notmatch '^\s*run=') {
        continue
    }

    $sample = [ordered]@{}
    if ($line -match '\bstep=(\d+)') {
        $sample.Step = [int]$Matches[1]
    }
    if ($line -match '\berr=(-?\d+)') {
        $sample.AngleErrorDeg = [double]$Matches[1] / 1000.0
    }
    if ($line -match '\bdriveMode=(-?\d+)/(-?\d+)') {
        # driveMode is the motor-output differential coordinate. Convert both
        # values to wheel rpm using the 40/55 * 60/15 = 32/11 gear ratio.
        $sample.DriveTargetRpm = ([double]$Matches[1] / 1000.0) * (32.0 / 11.0)
        $sample.DriveMeasuredRpm = ([double]$Matches[2] / 1000.0) * (32.0 / 11.0)
    }
    if ($line -match '\bm1=(-?\d+)/') {
        $sample.Motor1Rpm = [double]$Matches[1]
    }
    if ($line -match '\bm2=(-?\d+)/') {
        $sample.Motor2Rpm = [double]$Matches[1]
    }
    if ($line -match '\bt1=(\d+)') {
        $sample.Motor1TempC = [double]$Matches[1]
    }
    if ($line -match '\bt2=(\d+)') {
        $sample.Motor2TempC = [double]$Matches[1]
    }
    if ($line -match '\bscale=(\d+)') {
        $sample.TorqueScalingActive = [int]$Matches[1]
    }
    $samples.Add([pscustomobject]$sample)
}

$stopReason = if ($stopIndex -ge 0) {
    ($lines[$stopIndex] -replace '^\s*STOP:\s*', '').Trim()
}
else {
    "capture duration elapsed (no STOP)"
}

$angleErrors = @($samples | Where-Object {
    $null -ne $_.PSObject.Properties['AngleErrorDeg']
} | ForEach-Object { [Math]::Abs($_.AngleErrorDeg) })
$maxAngleError = if ($angleErrors.Count -gt 0) {
    ($angleErrors | Measure-Object -Maximum).Maximum
}
else {
    $null
}

$finalStart = [Math]::Floor($samples.Count / 2)
$finalHalf = if ($samples.Count -gt 0) {
    @($samples[$finalStart..($samples.Count - 1)])
}
else {
    @()
}
$driveTarget = @($finalHalf | Where-Object {
    $null -ne $_.PSObject.Properties['DriveTargetRpm']
} | ForEach-Object { $_.DriveTargetRpm })
$driveMeasured = @($finalHalf | Where-Object {
    $null -ne $_.PSObject.Properties['DriveMeasuredRpm']
} | ForEach-Object { $_.DriveMeasuredRpm })
$targetStats = Get-Stats -Values $driveTarget
$measuredStats = Get-Stats -Values $driveMeasured

Write-Host ("Log: {0}" -f $logPath)
Write-Host ("STOP: {0}; samples={1}" -f $stopReason, $samples.Count)
if ($null -ne $maxAngleError) {
    Write-Host ("max |angle error|: {0:F3} deg" -f $maxAngleError)
}
else {
    Write-Host "max |angle error|: n/a"
}
if (($null -ne $targetStats) -and ($null -ne $measuredStats)) {
    Write-Host ("final-half wheel rpm: target min/max/mean={0:F3}/{1:F3}/{2:F3}; measured={3:F3}/{4:F3}/{5:F3}" -f `
        $targetStats.Min, $targetStats.Max, $targetStats.Mean,
        $measuredStats.Min, $measuredStats.Max, $measuredStats.Mean)
}
else {
    Write-Host "final-half wheel rpm: n/a"
}

$stepSamples = @($samples | Where-Object {
    ($null -ne $_.PSObject.Properties['Step']) -and
    ($null -ne $_.PSObject.Properties['DriveTargetRpm']) -and
    ($null -ne $_.PSObject.Properties['DriveMeasuredRpm'])
})
if ($stepSamples.Count -gt 0) {
    Write-Host "per-step final-half wheel rpm:"
    $stepSamples |
        Group-Object -Property Step |
        Sort-Object { [int]$_.Name } |
        ForEach-Object {
            $group = @($_.Group)
            $groupFinalStart = [Math]::Floor($group.Count / 2)
            $groupFinal = @($group[$groupFinalStart..($group.Count - 1)])
            $groupTarget = @($groupFinal | ForEach-Object { $_.DriveTargetRpm })
            $groupMeasured = @($groupFinal | ForEach-Object { $_.DriveMeasuredRpm })
            $groupAngle = @($groupFinal | Where-Object {
                $null -ne $_.PSObject.Properties['AngleErrorDeg']
            } | ForEach-Object { [Math]::Abs($_.AngleErrorDeg) })
            $groupScaling = @($group | Where-Object {
                ($null -ne $_.PSObject.Properties['TorqueScalingActive']) -and
                ($_.TorqueScalingActive -ne 0)
            })
            $groupTemps = @($group | ForEach-Object {
                if ($null -ne $_.PSObject.Properties['Motor1TempC']) { $_.Motor1TempC }
                if ($null -ne $_.PSObject.Properties['Motor2TempC']) { $_.Motor2TempC }
            })
            $groupMaxTemp = if ($groupTemps.Count -gt 0) {
                ($groupTemps | Measure-Object -Maximum).Maximum
            }
            else {
                $null
            }
            $groupTargetStats = Get-Stats -Values $groupTarget
            $groupMeasuredStats = Get-Stats -Values $groupMeasured
            $groupMaxAngle = if ($groupAngle.Count -gt 0) {
                ($groupAngle | Measure-Object -Maximum).Maximum
            }
            else {
                $null
            }
            if (($null -ne $groupTargetStats) -and ($null -ne $groupMeasuredStats)) {
                Write-Host ("  step {0}: targetMean={1:F3}; measured min/max/mean={2:F3}/{3:F3}/{4:F3}; p-p={5:F3}; maxAngle={6:F3}; scaling={7:P1}; maxTemp={8}; n={9}" -f `
                    $_.Name,
                    $groupTargetStats.Mean,
                    $groupMeasuredStats.Min,
                    $groupMeasuredStats.Max,
                    $groupMeasuredStats.Mean,
                    ($groupMeasuredStats.Max - $groupMeasuredStats.Min),
                    $groupMaxAngle,
                    ($groupScaling.Count / $group.Count),
                    $(if ($null -ne $groupMaxTemp) { "{0:F0}C" -f $groupMaxTemp } else { "n/a" }),
                    $group.Count)
            }
        }
}
else {
    Write-Host "per-step final-half wheel rpm: n/a"
}

$motorSamples = @($samples | Where-Object {
    ($null -ne $_.PSObject.Properties['Motor1Rpm']) -and
    ($null -ne $_.PSObject.Properties['Motor2Rpm'])
})
if ($motorSamples.Count -gt 0) {
    $m1Nonzero = @($motorSamples | Where-Object { $_.Motor1Rpm -ne 0 }).Count
    $m2Nonzero = @($motorSamples | Where-Object { $_.Motor2Rpm -ne 0 }).Count
    Write-Host ("motor rpm nonzero: m1={0:P1} m2={1:P1} (n={2})" -f `
        ($m1Nonzero / $motorSamples.Count),
        ($m2Nonzero / $motorSamples.Count),
        $motorSamples.Count)
}
else {
    Write-Host "motor rpm nonzero: n/a"
}
