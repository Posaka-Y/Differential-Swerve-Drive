<#
.SYNOPSIS
    Windows 開発環境を winget で一括導入する(CLI完結、対話なし)。

.DESCRIPTION
    ビルドと書き込みに必要なツールを winget から入れる。既に入っているものは
    スキップするので、何度実行しても安全。

    入るもの:
      Arm.GnuArmEmbeddedToolchain   クロスコンパイラ (AGENTS.md 指定の 14.2)
      Kitware.CMake                 ビルド構成
      Ninja-build.Ninja             ビルド実行
      xpack-dev-tools.openocd-xpack SWD 接続・書き込み (ST のログイン不要)

    ST-Link のデバッグI/F ドライバだけは winget に無い。-WithZadig を付けると
    Zadig も入れるが、ドライバの割り当て自体は GUI 操作が1回だけ必要になる。

    実行後は firmware/scripts/doctor.ps1 で状態を確認すること。

.EXAMPLE
    .\firmware\scripts\setup-windows.ps1
    .\firmware\scripts\setup-windows.ps1 -WithZadig
    .\firmware\scripts\setup-windows.ps1 -WhatIf
#>
[CmdletBinding(SupportsShouldProcess = $true)]
param(
    # ST-Link のドライバ割り当て用 GUI ツールも入れる。
    [switch]$WithZadig
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    throw "winget was not found. Install 'App Installer' from the Microsoft Store first."
}

$packages = @(
    [ordered]@{ id = "Arm.GnuArmEmbeddedToolchain"; probe = "arm-none-eabi-gcc" },
    [ordered]@{ id = "Kitware.CMake"; probe = "cmake" },
    [ordered]@{ id = "Ninja-build.Ninja"; probe = "ninja" },
    [ordered]@{ id = "xpack-dev-tools.openocd-xpack"; probe = "openocd" }
)
if ($WithZadig) {
    $packages += [ordered]@{ id = "akeo.ie.Zadig"; probe = $null }
}

foreach ($package in $packages) {
    if ($package.probe -and (Get-Command $package.probe -ErrorAction SilentlyContinue)) {
        Write-Host "[skip] $($package.id) (already on PATH)" -ForegroundColor DarkGray
        continue
    }

    if (-not $PSCmdlet.ShouldProcess($package.id, "winget install")) { continue }

    Write-Host "[install] $($package.id)" -ForegroundColor Cyan
    # 同意を自動承諾しないと非対話で止まる。--silent はインストーラのUIを抑止する。
    & winget install --id $package.id --exact --silent `
        --accept-package-agreements --accept-source-agreements
    # 既に導入済みのとき winget は非0を返すので、失敗扱いにはしない。
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "winget returned $LASTEXITCODE for $($package.id). Check manually if the tool is missing afterwards."
    }
}

Write-Host "`nInstalled packages are visible to new shells only." -ForegroundColor Yellow
Write-Host "Open a fresh terminal, then run: .\firmware\scripts\doctor.ps1"

if ($WithZadig) {
    Write-Host @"

Zadig (one-time, GUI):
  1. Run Zadig as administrator
  2. Options -> List All Devices
  3. Select 'ST-Link Debug' (Interface 0)  <-- never pick the (COMx) interface
  4. Choose WinUSB, then Install Driver
"@ -ForegroundColor Yellow
}
