<#
.SYNOPSIS
    UART システムブートローダへ接続し、MCU が生きているかを判定する(書き込みはしない)。

.DESCRIPTION
    SWD が使えない状況で「MCU そのものが起動しているか」を切り分けるための試験。
    外部ツールを一切使わず .NET の SerialPort だけで完結するので、導入物ゼロで走る。

    STM32 のシステムブートローダは 8bit/even parity/1stop で待ち受け、ホストが
    0x7F を1バイト送ると 0x79 (ACK) を返す。これが返れば以下が同時に確定する:
      - MCU コアが起動している (電源・GND・内部レギュレータが生きている)
      - BOOT0 が正しく High でサンプルされている
      - PA2/PA3 のはんだ付けと J7 の配線が生きている

    NACK(0x1F) は「ブートローダは応答したが直前のコマンドが不正」の意味で、
    これも MCU 生存の証拠になる。

    事前準備:
      1. BOOT0 テストポイントを隣接 3V3 テストポイントへ短絡する
         (BOOT0 は reset 時にサンプルされるので、短絡してから電源を入れ直す)
      2. USB-シリアルを J7 へ配線する。TX/RX はクロス:
           probe TXD -> J7 pin6 (DBG_RX = PA3)
           probe RXD -> J7 pin5 (DBG_TX = PA2)
           GND       -> J7 pin1
      3. 基板へ 5V を給電する (J1)。デバッガからは給電されない
      4. 電源を入れ直してから実行する

.EXAMPLE
    .\firmware\scripts\bootloader-ping.ps1
    .\firmware\scripts\bootloader-ping.ps1 -Port COM5 -Json
#>
[CmdletBinding()]
param(
    # 省略時は COM ポートが1つだけならそれを使う。複数あるときは明示が必要。
    [string]$Port,

    # 省略時は複数のボーレートを順に試す。システムブートローダは自動検出するので、
    # 1回の実行で取りこぼしを潰せるほうが実機では速い。
    [int]$BaudRate = 0,

    # 取りこぼし対策に既定で複数回試す。1回目は自動ボーレート検出で捨てられることがある。
    [ValidateRange(1, 20)]
    [int]$Attempts = 5,

    [ValidateRange(100, 10000)]
    [int]$TimeoutMs = 1000,

    # USB-シリアル側だけを切り分ける。プローブの TXD と RXD を直結してから実行し、
    # 送ったバイトがそのまま返るかを見る。基板を外した状態で行う。
    [switch]$Loopback,

    [switch]$Json
)

$ErrorActionPreference = "Stop"

$SYNC = [byte]0x7F
$ACK = 0x79
$NACK = 0x1F

if (-not $Port) {
    # @() で必ず配列にする。1個だけのとき文字列になり [0] が先頭文字を返す。
    $available = @([System.IO.Ports.SerialPort]::GetPortNames() | Sort-Object)
    if ($available.Count -eq 0) { throw "No serial ports found. Connect the USB-serial adapter first." }
    if ($available.Count -gt 1) {
        throw ("Multiple serial ports found ({0}). Specify one with -Port." -f ($available -join ", "))
    }
    $Port = $available[0]
}

$result = [ordered]@{
    port      = $Port
    baudRate  = $BaudRate
    alive     = $false
    response  = $null
    attempts  = 0
    verdict   = $null
    tried     = @()
}

# 0 指定(既定)なら複数を順に試す。実機では1回の実行で潰せるほうが速い。
$baudCandidates = if ($BaudRate -gt 0) { @($BaudRate) } else { @(115200, 57600, 38400, 19200, 9600) }

foreach ($baud in $baudCandidates) {
$result.baudRate = $baud
$result.tried += $baud
$serial = New-Object System.IO.Ports.SerialPort $Port, $baud, ([System.IO.Ports.Parity]::Even), 8, ([System.IO.Ports.StopBits]::One)
$serial.ReadTimeout = $TimeoutMs
$serial.WriteTimeout = $TimeoutMs

try {
    $serial.Open()
    # 直前の残骸が ACK に見えるのを防ぐ。
    $serial.DiscardInBuffer()
    $serial.DiscardOutBuffer()

    if ($Loopback) {
        # 基板を介さず USB-シリアル単体の往復だけを見る。
        $pattern = [byte[]]@(0x55, 0xAA, 0x01, 0x7F)
        $echoed = @()
        $serial.Write($pattern, 0, $pattern.Length)
        foreach ($expected in $pattern) {
            try { $echoed += $serial.ReadByte() } catch [TimeoutException] { break }
        }
        $ok = ($echoed.Count -eq $pattern.Length) -and
              (-not (Compare-Object $echoed $pattern -SyncWindow 0))
        $result.alive = $ok
        $result.response = (($echoed | ForEach-Object { $_.ToString("X2") }) -join " ")
        $result.verdict = if ($ok) {
            "Loopback OK - the USB-serial path works. Any silence afterwards is on the board side."
        }
        else {
            "Loopback FAILED - the adapter, cable or COM port is the problem, not the board. Confirm TXD and RXD are actually shorted."
        }
    }
    else {

    for ($i = 1; $i -le $Attempts; $i++) {
        $result.attempts = $i
        $serial.Write(@($SYNC), 0, 1)
        try {
            $byte = $serial.ReadByte()
        }
        catch [TimeoutException] {
            continue
        }

        $result.response = ("0x{0:X2}" -f $byte)
        if ($byte -eq $ACK) {
            $result.alive = $true
            $result.verdict = "ACK - bootloader responded. The MCU is running."
            break
        }
        if ($byte -eq $NACK) {
            # 既に同期済みのブートローダは 0x7F 再送を NACK で返す。これも生存の証拠。
            $result.alive = $true
            $result.verdict = "NACK - bootloader is present but already synchronised. The MCU is running."
            break
        }
        $result.verdict = "Unexpected byte. Check TX/RX orientation and that nothing else drives the line."
    }

    if (-not $result.alive -and -not $result.response) {
        $result.verdict = "No response. Check BOOT0 high at reset, the 5 V supply, TX/RX crossing, and common GND."
    }

    }
}
finally {
    if ($serial.IsOpen) { $serial.Close() }
    $serial.Dispose()
}

if ($result.alive) { break }
# ループバックはボーレートを変えても意味が変わらないので1回で打ち切る。
if ($Loopback) { break }
}

if ($Json) {
    $result | ConvertTo-Json -Depth 3
}
else {
    Write-Host "=== bootloader ping ===" -ForegroundColor Cyan
    Write-Host ("port     : {0} @ {1} 8E1" -f $result.port, $result.baudRate)
    Write-Host ("attempts : {0}" -f $result.attempts)
    Write-Host ("response : {0}" -f $(if ($result.response) { $result.response } else { "(none)" }))
    Write-Host ("alive    : {0}" -f $(if ($result.alive) { "YES" } else { "NO" })) -ForegroundColor $(if ($result.alive) { "Green" } else { "Yellow" })
    Write-Host ("verdict  : {0}" -f $result.verdict)
}

if (-not $result.alive) { exit 1 }
exit 0
