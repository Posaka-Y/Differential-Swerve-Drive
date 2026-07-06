[CmdletBinding()]
param(
    [string]$Port,
    [ValidateRange(1200, 3000000)]
    [int]$BaudRate = 115200,
    [ValidateRange(0, 86400)]
    [int]$DurationSeconds = 0,
    # 閉ループ試験ログを検出して収束/STOP後に自動終了する(未指定なら従来通り)
    [switch]$EarlyExit,
    # 接続直後のVCPバッファ再生に含まれる古いSTART行を無視する期間
    [ValidateRange(0, 60)]
    [int]$StartIgnoreSeconds = 5,
    # 収束判定に必要な連続安定サンプル数(ログは250ms周期)
    [ValidateRange(1, 100)]
    [int]$StableSamples = 4,
    # 判定確定後も末尾データを取り続ける秒数
    [ValidateRange(0, 60)]
    [double]$TailSeconds = 2
)

$ErrorActionPreference = "Stop"

# 閉ループ試験ログ1行を評価して $State を更新する。
# 判定基準は .claude/skills/gain-tuning/SKILL.md と同一:
#   収束 = |err| < 500 かつ steer=0 が StableSamples 連続
#   STOP: 行 = ファーム側の停止ラッチ
# StartIgnoreSeconds 以前の START 行は前回ファームのバッファ再生とみなして捨てる
# (旧ファームはSTARTを起動時に1回しか出さないため、それ以降のSTARTは今回の試験)。
function Update-EarlyExitState {
    param(
        [hashtable]$State,
        [string]$Line,
        [double]$ElapsedSeconds,
        [int]$StartIgnoreSeconds,
        [int]$StableSamples
    )

    if ($Line -match '^\s*START:') {
        if ($ElapsedSeconds -ge $StartIgnoreSeconds) {
            $State.Started = $true
            $State.Stable = 0
            $State.Decided = $false
            $State.Reason = $null
        }
        return
    }

    if (-not $State.Started -or $State.Decided) {
        return
    }

    if ($Line -match '^\s*STOP:') {
        $State.Decided = $true
        $State.DecidedAt = $ElapsedSeconds
        $State.Reason = "STOP"
        return
    }

    if ($Line -match 'err=(-?\d+)' ) {
        $err = [int]$Matches[1]
        if ($Line -match '\bsteer=(-?[0-9.]+)') {
            $steer = [double]$Matches[1]
            if (([Math]::Abs($err) -lt 500) -and ($steer -eq 0)) {
                $State.Stable++
                if ($State.Stable -ge $StableSamples) {
                    $State.Decided = $true
                    $State.DecidedAt = $ElapsedSeconds
                    $State.Reason = "converged"
                }
            }
            else {
                $State.Stable = 0
            }
        }
    }
}

if (-not $Port) {
    $stLinkPorts = @(Get-CimInstance Win32_SerialPort | Where-Object {
        $_.Name -like "*STLink Virtual COM Port*"
    })
    if ($stLinkPorts.Count -ne 1) {
        $available = @(Get-CimInstance Win32_SerialPort | ForEach-Object {
            "$($_.DeviceID): $($_.Name)"
        }) -join "`n"
        throw "Specify -Port. Expected one STLink VCP, found $($stLinkPorts.Count).`n$available"
    }
    $Port = $stLinkPorts[0].DeviceID
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

Write-Host "Opening $Port at $BaudRate baud (8N1). Press Ctrl+C to stop."
$serial.Open()
$start = [System.Diagnostics.Stopwatch]::StartNew()

$state = @{
    Started   = $false
    Stable    = 0
    Decided   = $false
    DecidedAt = 0.0
    Reason    = $null
}
$pending = ""

try {
    while (($DurationSeconds -eq 0) -or
           ($start.Elapsed.TotalSeconds -lt $DurationSeconds)) {
        $text = $serial.ReadExisting()
        if ($text.Length -gt 0) {
            [Console]::Write($text)
            if ($EarlyExit) {
                $pending += $text
                while (($nl = $pending.IndexOf("`n")) -ge 0) {
                    $line = $pending.Substring(0, $nl).TrimEnd("`r")
                    $pending = $pending.Substring($nl + 1)
                    Update-EarlyExitState -State $state -Line $line `
                        -ElapsedSeconds $start.Elapsed.TotalSeconds `
                        -StartIgnoreSeconds $StartIgnoreSeconds `
                        -StableSamples $StableSamples
                }
            }
        }
        if ($EarlyExit -and $state.Decided -and
            (($start.Elapsed.TotalSeconds - $state.DecidedAt) -ge $TailSeconds)) {
            Write-Host ("`nEarlyExit: {0} at {1}s" -f $state.Reason,
                [Math]::Round($state.DecidedAt, 2))
            break
        }
        Start-Sleep -Milliseconds 20
    }
}
finally {
    if ($serial.IsOpen) {
        $serial.Close()
    }
    $serial.Dispose()
}
