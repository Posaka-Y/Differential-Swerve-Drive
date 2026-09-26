<#
.SYNOPSIS
    STM32 の UART システムブートローダ経由で .bin を書き込む(SWD不要、導入物ゼロ)。

.DESCRIPTION
    ST の AN3155 (USART protocol used in the STM32 bootloader) を直接実装している。
    外部ツールを入れずに .NET の SerialPort だけで完結するので、SWD プローブが
    使えない状況でも書き込める。

    使うコマンド:
      0x7F        同期
      0x02 Get ID 接続先 MCU の Product ID を確認 (書き込み前の取り違え防止)
      0x44 Extended Erase (mass erase)
      0x31 Write Memory   256 バイトずつ
      0x11 Read Memory    -Verify 指定時のみ
      0x21 Go             -Run 指定時のみ

    ブートローダは ROM にあり書き換わらないので、失敗しても同じ手順でやり直せる。

    事前準備は bootloader-ping.ps1 と同じ:
      1. BOOT0 テストポイントを隣接 3V3 へ短絡してから電源を入れ直す
      2. probe TXD -> J7 pin6 (PA3), probe RXD -> J7 pin5 (PA2), GND -> J7 pin1
      3. 基板へ 5V 給電 (J1)

    書き込み後は BOOT0 の短絡を外して電源を入れ直すとユーザーファームが起動する。

.EXAMPLE
    .\firmware\scripts\flash-uart.ps1 -Image blink
    .\firmware\scripts\flash-uart.ps1 -Image blink -Verify -Run
    .\firmware\scripts\flash-uart.ps1 -Image firmware -Port COM5
#>
[CmdletBinding()]
param(
    # blink = 一次確認用の最小ファーム、firmware = 本体ファーム。
    [ValidateSet("blink", "firmware")]
    [string]$Image = "blink",

    [ValidateSet("Debug", "Release")]
    [string]$Configuration = "Debug",

    # 省略時は COM ポートが1つだけならそれを使う。
    [string]$Port,

    [ValidateRange(1200, 115200)]
    [int]$BaudRate = 115200,

    # 書き込み後に読み戻して全バイト比較する。
    [switch]$Verify,

    # 書き込み後に Go コマンドでユーザーコードへ飛ばす。
    # BOOT0 を短絡したままなので、電源を入れ直すとまたブートローダに戻る。
    [switch]$Run,

    [ValidateRange(500, 30000)]
    [int]$TimeoutMs = 3000,

    # プロトコル組み立て部分だけを検証して終了する(ハードウェア不要)。
    [switch]$SelfTest
)

$ErrorActionPreference = "Stop"
$firmwareRoot = Split-Path -Parent $PSScriptRoot
$preset = $Configuration.ToLowerInvariant()

$FLASH_BASE = 0x08000000
$ACK = 0x79
$NACK = 0x1F
$CHUNK = 256

# STM32G474 の Product ID。取り違えて別基板へ書くのを防ぐ。
$EXPECTED_PID = 0x469

if (-not $SelfTest) {
    $imageName = if ($Image -eq "blink") { "blink" } else { "differential_swerve_firmware" }
    $imagePath = Join-Path $firmwareRoot "build/$preset/$imageName.bin"
    if (-not (Test-Path -LiteralPath $imagePath)) {
        throw "Image not found: $imagePath  (run firmware/scripts/build.ps1 first)"
    }

    $bytes = [System.IO.File]::ReadAllBytes($imagePath)
    if ($bytes.Length -eq 0) { throw "Image is empty: $imagePath" }

    if (-not $Port) {
        # @() で必ず配列にする。1個だけのとき文字列になり [0] が先頭文字を返す。
        $available = @([System.IO.Ports.SerialPort]::GetPortNames() | Sort-Object)
        if ($available.Count -eq 0) { throw "No serial ports found." }
        if ($available.Count -gt 1) {
            throw ("Multiple serial ports found ({0}). Specify one with -Port." -f ($available -join ", "))
        }
        $Port = $available[0]
    }

    $serial = New-Object System.IO.Ports.SerialPort $Port, $BaudRate, ([System.IO.Ports.Parity]::Even), 8, ([System.IO.Ports.StopBits]::One)
    $serial.ReadTimeout = $TimeoutMs
    $serial.WriteTimeout = $TimeoutMs
}

function Send-Bytes {
    param([byte[]]$Data)
    $serial.Write($Data, 0, $Data.Length)
}

function Read-Byte {
    param([string]$What)
    try { return $serial.ReadByte() }
    catch [TimeoutException] { throw "Timeout waiting for $What." }
}

function Wait-Ack {
    param([string]$What)
    $byte = Read-Byte -What $What
    if ($byte -eq $ACK) { return }
    if ($byte -eq $NACK) { throw "NACK from bootloader during $What." }
    throw ("Unexpected byte 0x{0:X2} during {1}." -f $byte, $What)
}

function Send-Command {
    # 単バイトコマンドは「コマンド, その補数」の2バイトで送る(AN3155)。
    param([byte]$Command, [string]$What)
    Send-Bytes @([byte]$Command, [byte](0xFF - $Command))
    Wait-Ack -What $What
}

function Get-Checksum {
    param([byte[]]$Data, [byte]$Seed = 0)
    $sum = $Seed
    foreach ($b in $Data) { $sum = $sum -bxor $b }
    return [byte]$sum
}

function Get-AddressBytes {
    param([uint32]$Address)
    # ビッグエンディアン4バイト + XOR チェックサム。
    $addr = [byte[]]@(
        [byte](($Address -shr 24) -band 0xFF),
        [byte](($Address -shr 16) -band 0xFF),
        [byte](($Address -shr 8) -band 0xFF),
        [byte]($Address -band 0xFF)
    )
    return $addr + @(Get-Checksum -Data $addr)
}

if ($SelfTest) {
    # ハードウェアが無くても壊れを検出できる範囲(フレーム組み立て)だけを検証する。
    $failures = @()
    function Assert-Equal {
        # byte へ正規化してから比較する。PowerShell の -f "X2" は型によって
        # 0x 接頭辞の有無が変わるため、ToString("X2") で表記を固定する。
        param([string]$What, [byte[]]$Expected, [byte[]]$Actual)
        $e = ($Expected | ForEach-Object { $_.ToString("X2") }) -join " "
        $a = ($Actual | ForEach-Object { $_.ToString("X2") }) -join " "
        if ($e -ne $a) { $script:failures += "$What : expected [$e] got [$a]" }
    }

    # 単バイトコマンドの補数 (AN3155)
    foreach ($pair in @(@(0x02, 0xFD), @(0x11, 0xEE), @(0x21, 0xDE), @(0x31, 0xCE), @(0x44, 0xBB))) {
        Assert-Equal -What ("complement of 0x{0:X2}" -f $pair[0]) -Expected $pair[1] -Actual ([byte](0xFF - $pair[0]))
    }

    Assert-Equal -What "checksum 01^02" -Expected 0x03 -Actual (Get-Checksum -Data ([byte[]]@(0x01, 0x02)))
    Assert-Equal -What "checksum seeded" -Expected 0x02 -Actual (Get-Checksum -Data ([byte[]]@(0x01)) -Seed 0x03)
    Assert-Equal -What "address 0x08000000" -Expected ([byte[]]@(0x08, 0x00, 0x00, 0x00, 0x08)) -Actual (Get-AddressBytes -Address 0x08000000)
    Assert-Equal -What "address 0x08000100" -Expected ([byte[]]@(0x08, 0x00, 0x01, 0x00, 0x09)) -Actual (Get-AddressBytes -Address 0x08000100)
    # mass erase のチェックサムは 0xFF xor 0xFF = 0x00
    Assert-Equal -What "mass erase checksum" -Expected 0x00 -Actual (Get-Checksum -Data ([byte[]]@(0xFF, 0xFF)))

    # 792 バイトなら 256*3 + 24 の 4 チャンク
    $chunks = [int][Math]::Ceiling(792 / $CHUNK)
    Assert-Equal -What "chunk count for 792 bytes" -Expected 4 -Actual $chunks

    if ($failures.Count -gt 0) {
        $failures | ForEach-Object { Write-Host "FAIL $_" -ForegroundColor Red }
        exit 1
    }
    Write-Host "flash-uart self-test: all checks passed" -ForegroundColor Green
    exit 0
}

try {
    $serial.Open()
    $serial.DiscardInBuffer()
    $serial.DiscardOutBuffer()

    # --- 同期 ---
    Write-Host "Syncing with bootloader on $Port ..." -ForegroundColor Cyan
    $synced = $false
    for ($i = 0; $i -lt 5; $i++) {
        Send-Bytes @([byte]0x7F)
        try { $byte = $serial.ReadByte() } catch [TimeoutException] { continue }
        # 既に同期済みのブートローダは 0x7F 再送へ NACK を返す。どちらも生存の証拠。
        if ($byte -eq $ACK -or $byte -eq $NACK) { $synced = $true; break }
    }
    if (-not $synced) {
        throw "No response from bootloader. Check BOOT0 high at reset, TX/RX crossing, GND, and the 5 V supply."
    }

    # --- Get ID ---
    Send-Command -Command 0x02 -What "Get ID"
    $count = Read-Byte -What "Get ID length"
    $pid = 0
    for ($i = 0; $i -le $count; $i++) {
        $pid = ($pid -shl 8) -bor (Read-Byte -What "Get ID payload")
    }
    Wait-Ack -What "Get ID completion"
    Write-Host ("Product ID    : 0x{0:X3}" -f $pid)
    if ($pid -ne $EXPECTED_PID) {
        throw ("Connected MCU reports 0x{0:X3}, expected 0x{1:X3} (STM32G474). Refusing to write." -f $pid, $EXPECTED_PID)
    }

    Write-Host ("Image         : {0} ({1} bytes)" -f $imagePath, $bytes.Length)

    # --- Extended Erase (mass erase) ---
    Write-Host "Mass erasing ..." -ForegroundColor Cyan
    Send-Command -Command 0x44 -What "Extended Erase"
    # 0xFFFF = mass erase。続くチェックサムは 0xFF xor 0xFF = 0x00。
    $previousTimeout = $serial.ReadTimeout
    $serial.ReadTimeout = [Math]::Max($TimeoutMs, 20000)
    try {
        Send-Bytes @([byte]0xFF, [byte]0xFF, [byte]0x00)
        Wait-Ack -What "mass erase"
    }
    finally {
        $serial.ReadTimeout = $previousTimeout
    }

    # --- Write Memory ---
    $total = [Math]::Ceiling($bytes.Length / $CHUNK)
    Write-Host ("Writing {0} chunks ..." -f $total) -ForegroundColor Cyan
    for ($offset = 0; $offset -lt $bytes.Length; $offset += $CHUNK) {
        $length = [Math]::Min($CHUNK, $bytes.Length - $offset)
        $chunk = New-Object byte[] $length
        [Array]::Copy($bytes, $offset, $chunk, 0, $length)

        Send-Command -Command 0x31 -What "Write Memory"
        Send-Bytes (Get-AddressBytes -Address ([uint32]($FLASH_BASE + $offset)))
        Wait-Ack -What "write address"

        # 長さバイトは N-1。チェックサムは N-1 とデータ全部の XOR。
        $countByte = [byte]($length - 1)
        Send-Bytes (@($countByte) + $chunk + @(Get-Checksum -Data $chunk -Seed $countByte))
        Wait-Ack -What "write data"

        Write-Progress -Activity "Writing flash" -Status ("{0} / {1} bytes" -f ($offset + $length), $bytes.Length) `
            -PercentComplete (100.0 * ($offset + $length) / $bytes.Length)
    }
    Write-Progress -Activity "Writing flash" -Completed
    Write-Host "Write complete." -ForegroundColor Green

    # --- Verify ---
    if ($Verify) {
        Write-Host "Verifying ..." -ForegroundColor Cyan
        for ($offset = 0; $offset -lt $bytes.Length; $offset += $CHUNK) {
            $length = [Math]::Min($CHUNK, $bytes.Length - $offset)

            Send-Command -Command 0x11 -What "Read Memory"
            Send-Bytes (Get-AddressBytes -Address ([uint32]($FLASH_BASE + $offset)))
            Wait-Ack -What "read address"

            $countByte = [byte]($length - 1)
            Send-Bytes @($countByte, [byte](0xFF - $countByte))
            Wait-Ack -What "read length"

            for ($i = 0; $i -lt $length; $i++) {
                $actual = Read-Byte -What "read payload"
                if ($actual -ne $bytes[$offset + $i]) {
                    throw ("Verify failed at 0x{0:X8}: wrote 0x{1:X2}, read 0x{2:X2}." -f
                        ($FLASH_BASE + $offset + $i), $bytes[$offset + $i], $actual)
                }
            }
            Write-Progress -Activity "Verifying flash" -Status ("{0} / {1} bytes" -f ($offset + $length), $bytes.Length) `
                -PercentComplete (100.0 * ($offset + $length) / $bytes.Length)
        }
        Write-Progress -Activity "Verifying flash" -Completed
        Write-Host "Verify OK." -ForegroundColor Green
    }

    # --- Go ---
    if ($Run) {
        Write-Host "Jumping to user code ..." -ForegroundColor Cyan
        Send-Command -Command 0x21 -What "Go"
        Send-Bytes (Get-AddressBytes -Address ([uint32]$FLASH_BASE))
        Wait-Ack -What "go address"
        Write-Host "Running." -ForegroundColor Green
    }
}
finally {
    if ($serial.IsOpen) { $serial.Close() }
    $serial.Dispose()
}

Write-Host "`nRemove the BOOT0 short and power-cycle to boot the user firmware." -ForegroundColor Yellow
