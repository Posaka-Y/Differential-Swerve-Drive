<#
.SYNOPSIS
    SWD でターゲットへ接続し、生存確認の結果を返す(書き込みはしない)。

.DESCRIPTION
    OpenOCD があればそれを使い、無ければ STM32_Programmer_CLI へ落とす。
    どちらも GUI を出さずに終了するので、エージェントからそのまま叩ける。

    確認できること:
      - デバッグプローブが掴めているか
      - プローブ報告電圧 (WeAct MiniDebugger V1.0では内部3.3V相当。MCU電源ではない)
      - CPU コアが応答するか (はんだ・SWD配線・NRST が生きているか)

    ターゲットは基板ごとに変える:
      unit board (STM32G474RET6) -> stm32g4x   ※既定
      ODOM board (STM32F405RGT6) -> stm32f4x

.EXAMPLE
    .\firmware\scripts\probe.ps1
    .\firmware\scripts\probe.ps1 -Target stm32f4x
    .\firmware\scripts\probe.ps1 -Json
#>
[CmdletBinding()]
param(
    [ValidateSet("stm32g4x", "stm32f4x")]
    [string]$Target = "stm32g4x",

    # SWD クロック。配線が長い/不安定なときは下げる。
    [ValidateRange(5, 8000)]
    [int]$SpeedKHz = 1000,

    # NRST を掴んだまま接続する。ファームが即スリープ等に入る場合に使う。
    [switch]$UnderReset,

    [ValidateSet('dap', 'hla')]
    [string]$Interface = 'dap',

    [ValidatePattern('^[a-zA-Z0-9_-]*$')]
    [string]$Serial = '',

    [switch]$Trace,

    [ValidateRange(5, 300)]
    [int]$TimeoutSeconds = 30,

    [switch]$Json
)

$ErrorActionPreference = "Stop"

$previousWarning = $WarningPreference
$WarningPreference = "SilentlyContinue"
try { . (Join-Path $PSScriptRoot "toolchain.ps1") } finally { $WarningPreference = $previousWarning }

function Invoke-WithTimeout {
    param([string]$FilePath, [string[]]$Arguments, [int]$Seconds)

    $stdout = [System.IO.Path]::GetTempFileName()
    $stderr = [System.IO.Path]::GetTempFileName()
    try {
        # Start-Process joins ArgumentList with spaces. Quote EVERY argument using
        # Windows argv escaping, including paths, embedded quotes and trailing slashes.
        $quoted = foreach ($argument in $Arguments) {
            '"' + ([regex]::Replace([regex]::Replace($argument, '(\\*)"', '$1$1\"'), '(\\+)$', '$1$1')) + '"'
        }
        $process = Start-Process -FilePath $FilePath -ArgumentList ($quoted -join ' ') -NoNewWindow -PassThru `
            -RedirectStandardOutput $stdout -RedirectStandardError $stderr
        if (-not $process.WaitForExit($Seconds * 1000)) {
            # OpenOCD は掴んだまま常駐することがある。放置すると次回接続も塞ぐので必ず落とす。
            try { $process.Kill(); $process.WaitForExit() } catch { }
            return [ordered]@{ timedOut = $true; exitCode = $null; output = (Get-Content $stdout, $stderr -Raw -ErrorAction SilentlyContinue) -join "`n" }
        }
        $process.WaitForExit()
        $text = @(
            (Get-Content -LiteralPath $stdout -Raw -ErrorAction SilentlyContinue),
            (Get-Content -LiteralPath $stderr -Raw -ErrorAction SilentlyContinue)
        ) -join "`n"
        return [ordered]@{ timedOut = $false; exitCode = $process.ExitCode; output = $text }
    }
    finally {
        Remove-Item -LiteralPath $stdout, $stderr -Force -ErrorAction SilentlyContinue
    }
}

$result = [ordered]@{
    tool          = $null
    connected     = $false
    target        = $Target
    targetVoltage = $null
    idcode        = $null
    core          = $null
    timedOut      = $false
    output        = $null
    interface     = $Interface
    serial        = $Serial
    exitCode      = $null
    failureStage  = $null
    voltageNote   = 'Probe-reported target voltage.'
}

$openocd = Get-Command "openocd" -ErrorAction SilentlyContinue
$programmer = Get-Command "STM32_Programmer_CLI" -ErrorAction SilentlyContinue

if ($openocd) {
    $result.tool = "openocd"
    $scriptsDir = Resolve-OpenOcdScriptsDir -OpenOcdPath $openocd.Source

    $arguments = @()
    if ($scriptsDir) { $arguments += @("-s", $scriptsDir) }
    if ($Trace) { $arguments += '-d3' }
    $interfaceFile = if ($Interface -eq 'hla') { 'stlink-hla.cfg' } else { 'stlink.cfg' }
    $arguments += @("-f", "interface/$interfaceFile")
    $arguments += @("-c", 'transport select swd')
    if ($Serial) { $arguments += @('-c', "adapter serial $Serial") }
    $arguments += @("-f", "target/$Target.cfg")
    # target/*.cfg sets its own default speed/reset mode, so overrides must come afterwards.
    $arguments += @("-c", "adapter speed $SpeedKHz")
    if ($UnderReset) { $arguments += @("-c", 'reset_config srst_only srst_nogate connect_assert_srst') }
    else { $arguments += @('-c', 'reset_config none') }
    # init だけ通れば生存確認は足りる。halt までやると走行中のファームを止めてしまう。
    # A successful CPUID read is stronger evidence than a Cortex-M string in a log.
    $arguments += @("-c", 'init; targets; set cpuid [mrw 0xE000ED00]; echo [format "PROBE_CPUID=0x%08x" $cpuid]; shutdown')

    $run = Invoke-WithTimeout -FilePath $openocd.Source -Arguments $arguments -Seconds $TimeoutSeconds
    $result.timedOut = $run.timedOut
    $result.output = $run.output
    $result.exitCode = $run.exitCode

    if ($run.output -match 'Target voltage:\s*([0-9.]+)') { $result.targetVoltage = [double]$Matches[1] }
    if ($run.output -match 'VID:PID\s+0483:3752') {
        $result.voltageNote = 'WeAct MiniDebugger V1.0 has no target-VREF sense input; this is an internal value, not the target supply.'
    }
    if ($run.output -match 'IDCODE[^0-9a-fx]*(0x[0-9a-fA-F]+)') { $result.idcode = $Matches[1] }
    if ($run.output -match '(Cortex-M\d+[^\r\n]*)') { $result.core = $Matches[1].Trim() }
    $cpuidValid = $run.output -match '(?m)^PROBE_CPUID=0x41[0-9a-fA-F]fc24[0-9a-fA-F]\s*$'
    $result.connected = [bool](-not $run.timedOut -and $run.exitCode -eq 0 -and $cpuidValid)
    if ($run.timedOut) { $result.failureStage = 'timeout' }
    elseif ($run.output -match 'STLINK_JTAG_GET_IDCODE_ERROR|init mode failed') { $result.failureStage = 'debug-entry/idcode' }
    elseif (-not $result.connected) { $result.failureStage = 'tool-or-target-examination' }
}
elseif ($programmer) {
    $result.tool = "STM32_Programmer_CLI"
    $arguments = @("-c", "port=SWD", "freq=$SpeedKHz")
    if ($UnderReset) { $arguments += "mode=UR" }

    $run = Invoke-WithTimeout -FilePath $programmer.Source -Arguments $arguments -Seconds $TimeoutSeconds
    $result.timedOut = $run.timedOut
    $result.output = $run.output
    $result.exitCode = $run.exitCode

    if ($run.output -match 'Device ID\s*:\s*(0x[0-9a-fA-F]+)') { $result.idcode = $Matches[1] }
    if ($run.output -match 'Device name\s*:\s*([^\r\n]+)') { $result.core = $Matches[1].Trim() }
    $result.connected = [bool](-not $run.timedOut -and $run.exitCode -eq 0 -and $result.idcode)
}
else {
    $result.output = "Neither openocd nor STM32_Programmer_CLI was found. Run firmware/scripts/setup-windows.ps1 first."
}

if ($Json) {
    $result | ConvertTo-Json -Depth 4
}
else {
    Write-Host "=== probe ($($result.tool)) ===" -ForegroundColor Cyan
    Write-Host ("connected     : {0}" -f $(if ($result.connected) { "YES" } else { "NO" }))
    Write-Host ("target        : {0}" -f $result.target)
    Write-Host ("probe voltage : {0}" -f $(if ($null -ne $result.targetVoltage) { "$($result.targetVoltage) V" } else { "(unknown)" }))
    Write-Host ("voltage note  : {0}" -f $result.voltageNote)
    Write-Host ("idcode        : {0}" -f $(if ($result.idcode) { $result.idcode } else { "(unknown)" }))
    Write-Host ("core          : {0}" -f $(if ($result.core) { $result.core } else { "(unknown)" }))
    if (-not $result.connected) {
        Write-Host "`n-- tool output --" -ForegroundColor Yellow
        Write-Host $result.output
    }
}

if (-not $result.connected) { exit 1 }
exit 0
