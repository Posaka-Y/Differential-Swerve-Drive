<#
.SYNOPSIS
    ファーム開発環境の状態を1コマンドで報告する(読み取り専用)。

.DESCRIPTION
    ツールチェーン、デバッグプローブ、シリアルポート、ビルド成果物の状態を
    まとめて出力する。何も変更しないので、いつ実行しても安全。

    AI エージェントから使う場合は -Json を付けて機械可読出力にする。

.EXAMPLE
    .\firmware\scripts\doctor.ps1
    .\firmware\scripts\doctor.ps1 -Json
#>
[CmdletBinding()]
param(
    # 機械可読出力。人間向けの整形を省いて JSON だけを出す。
    [switch]$Json
)

$ErrorActionPreference = "Stop"
$firmwareRoot = Split-Path -Parent $PSScriptRoot

# toolchain.ps1 は見つからないツールについて Write-Warning を出す。
# doctor 自身が欠落を報告するので、ここでは警告を飲み込む。
$previousWarning = $WarningPreference
$WarningPreference = "SilentlyContinue"
try { . (Join-Path $PSScriptRoot "toolchain.ps1") } finally { $WarningPreference = $previousWarning }

function Get-ToolInfo {
    param(
        [string]$Name,
        [string[]]$VersionArgs = @("--version"),
        [switch]$Required
    )

    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $command) {
        return [ordered]@{ name = $Name; found = $false; required = [bool]$Required; path = $null; version = $null }
    }

    $version = $null
    try {
        $raw = & $command.Source @VersionArgs 2>&1 | Out-String
        # 1行目だけ採る。どのツールも先頭行に版番号を出す。
        $version = ($raw -split "`r?`n" | Where-Object { $_.Trim() } | Select-Object -First 1).Trim()
    }
    catch {
        $version = "(version query failed)"
    }

    [ordered]@{
        name     = $Name
        found    = $true
        required = [bool]$Required
        path     = $command.Source
        version  = $version
    }
}

$tools = @(
    (Get-ToolInfo -Name "arm-none-eabi-gcc" -Required),
    (Get-ToolInfo -Name "cmake" -Required),
    (Get-ToolInfo -Name "ninja" -Required),
    (Get-ToolInfo -Name "openocd"),
    (Get-ToolInfo -Name "STM32_Programmer_CLI" -VersionArgs @("--version"))
)

# --- デバッグプローブ (USB列挙とドライバ状態) ---
# ST-Link は複合デバイス。デバッグI/F(MI_00)と仮想COM(MI_01)は別々に
# ドライバが当たるため、片方だけ壊れている状態を見分ける必要がある。
$probes = @()
try {
    foreach ($device in (Get-PnpDevice -PresentOnly -ErrorAction SilentlyContinue |
            Where-Object { $_.InstanceId -match 'VID_0483' })) {
        $props = Get-PnpDeviceProperty -InstanceId $device.InstanceId -ErrorAction SilentlyContinue
        $problem = ($props | Where-Object KeyName -eq 'DEVPKEY_Device_ProblemCode').Data
        $driver = ($props | Where-Object KeyName -eq 'DEVPKEY_Device_DriverDesc').Data
        $probes += [ordered]@{
            name       = $device.FriendlyName
            status     = [string]$device.Status
            problem    = $problem
            driver     = $driver
            instanceId = $device.InstanceId
            # 28 = ドライバ未インストール。ここが立っていると接続系は全部失敗する。
            hint       = if ($problem -eq 28) { "driver not installed (code 28)" } else { $null }
        }
    }
}
catch {
    $probes = @()
}

# --- シリアルポート ---
$serialPorts = @()
try {
    foreach ($port in (Get-CimInstance Win32_PnPEntity -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -match '\(COM\d+\)' })) {
        if ($port.Name -match '\((COM\d+)\)') {
            $serialPorts += [ordered]@{ port = $Matches[1]; name = $port.Name }
        }
    }
}
catch {
    $serialPorts = @()
}

# --- ビルド成果物 ---
$artifacts = @()
foreach ($preset in @("debug", "release")) {
    $elf = Join-Path $firmwareRoot "build/$preset/differential_swerve_firmware.elf"
    $hex = Join-Path $firmwareRoot "build/$preset/differential_swerve_firmware.hex"
    $item = if (Test-Path -LiteralPath $elf) { Get-Item -LiteralPath $elf } else { $null }
    $artifacts += [ordered]@{
        preset   = $preset
        elf      = if ($item) { $elf } else { $null }
        hex      = if (Test-Path -LiteralPath $hex) { $hex } else { $null }
        builtAt  = if ($item) { $item.LastWriteTime.ToString("s") } else { $null }
    }
}

# --- 総合判定 ---
$missingRequired = @($tools | Where-Object { $_.required -and -not $_.found } | ForEach-Object { $_.name })
$canFlash = [bool](($tools | Where-Object { $_.name -in @("openocd", "STM32_Programmer_CLI") -and $_.found }).Count)
$debugProbe = $probes | Where-Object { $_.name -match 'Debug' } | Select-Object -First 1
$probeReady = [bool]($debugProbe -and $debugProbe.problem -eq 0)

$report = [ordered]@{
    generatedAt     = (Get-Date).ToString("s")
    canBuild        = ($missingRequired.Count -eq 0)
    canFlash        = $canFlash
    probeReady      = $probeReady
    missingRequired = $missingRequired
    tools           = $tools
    probes          = $probes
    serialPorts     = $serialPorts
    artifacts       = $artifacts
}

if ($Json) {
    $report | ConvertTo-Json -Depth 6
    return
}

Write-Host "=== firmware doctor ===" -ForegroundColor Cyan
Write-Host ("build : {0}" -f $(if ($report.canBuild) { "OK" } else { "NG (missing: " + ($missingRequired -join ", ") + ")" }))
Write-Host ("flash : {0}" -f $(if ($canFlash) { "OK" } else { "NG (need openocd or STM32_Programmer_CLI)" }))
Write-Host ("probe driver : {0}" -f $(if ($probeReady) { "OK (USB only; MCU connection NOT tested)" } elseif ($debugProbe) { "NG (" + $debugProbe.hint + ")" } else { "NG (no ST-Link detected)" }))

Write-Host "`n-- tools --"
foreach ($tool in $tools) {
    $mark = if ($tool.found) { "[x]" } elseif ($tool.required) { "[ ] REQUIRED" } else { "[ ] optional" }
    Write-Host ("{0,-14} {1} {2}" -f $tool.name, $mark, $tool.version)
}

Write-Host "`n-- probes --"
if (-not $probes) { Write-Host "(none)" }
foreach ($probe in $probes) {
    Write-Host ("{0,-30} status={1} problem={2} {3}" -f $probe.name, $probe.status, $probe.problem, $probe.hint)
}

Write-Host "`n-- serial --"
if (-not $serialPorts) { Write-Host "(none)" }
foreach ($port in $serialPorts) { Write-Host ("{0}  {1}" -f $port.port, $port.name) }

Write-Host "`n-- build artifacts --"
foreach ($artifact in $artifacts) {
    $state = if ($artifact.elf) { $artifact.builtAt } else { "(not built)" }
    Write-Host ("{0,-8} {1}" -f $artifact.preset, $state)
}
