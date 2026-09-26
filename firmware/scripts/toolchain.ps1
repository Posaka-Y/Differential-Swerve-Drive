# Dot-source this file to make the firmware toolchain available on PATH.
# Resolves tools in this order:
#   1. Already on PATH
#   2. STM32Cube VS Code extension bundles (%LOCALAPPDATA%\stm32cube\bundles)
#   3. Arm GNU Toolchain default install locations (winget / official installer)

function Add-ToolDirToPath {
    param([string]$Directory)
    if ($Directory -and (Test-Path -LiteralPath $Directory) -and (";$env:PATH;" -notlike "*;$Directory;*")) {
        $env:PATH = "$Directory;$env:PATH"
    }
}

function Find-NewestBundleBin {
    param([string]$BundleName)
    $bundleRoot = Join-Path $env:LOCALAPPDATA "stm32cube/bundles/$BundleName"
    if (-not (Test-Path -LiteralPath $bundleRoot)) { return $null }
    $newest = Get-ChildItem -LiteralPath $bundleRoot -Directory |
        Sort-Object Name -Descending | Select-Object -First 1
    if (-not $newest) { return $null }
    $bin = Join-Path $newest.FullName "bin"
    if (Test-Path -LiteralPath $bin) { return $bin }
    return $null
}

function Resolve-FirmwareTool {
    param(
        [string]$Executable,
        [string[]]$CandidateDirectories
    )
    if (Get-Command $Executable -ErrorAction SilentlyContinue) { return $true }
    foreach ($dir in $CandidateDirectories) {
        if (-not $dir) { continue }
        foreach ($resolved in (Resolve-Path $dir -ErrorAction SilentlyContinue)) {
            if (Test-Path -LiteralPath (Join-Path $resolved.Path "$Executable.exe")) {
                Add-ToolDirToPath $resolved.Path
                return $true
            }
        }
    }
    return $false
}

function Resolve-OpenOcdScriptsDir {
    <#
      OpenOCD は設定ファイル(interface/*.cfg, target/*.cfg)の置き場所を知らないと
      起動できない。xPack は <root>/openocd/scripts、公式ビルドは
      <root>/share/openocd/scripts に置く。
    #>
    param([string]$OpenOcdPath)

    $binDir = Split-Path -Parent $OpenOcdPath
    $root = Split-Path -Parent $binDir
    foreach ($candidate in @(
            (Join-Path $root "openocd/scripts"),
            (Join-Path $root "share/openocd/scripts"),
            (Join-Path $root "scripts"))) {
        if (Test-Path -LiteralPath $candidate) { return $candidate }
    }
    return $null
}

$script:missingTools = @()

# winget インストール分の置き場所。winget は shim を Links へ置くが、
# 実体側も見ておくと shim が壊れていても解決できる。
$script:WinGetLinks = Join-Path $env:LOCALAPPDATA "Microsoft/WinGet/Links"
$script:WinGetPackages = Join-Path $env:LOCALAPPDATA "Microsoft/WinGet/Packages"

if (-not (Resolve-FirmwareTool "cmake" @(
    (Find-NewestBundleBin "cmake"),
    $script:WinGetLinks,
    "$env:ProgramFiles\CMake\bin"
))) { $script:missingTools += "cmake" }

if (-not (Resolve-FirmwareTool "ninja" @(
    (Find-NewestBundleBin "ninja"),
    $script:WinGetLinks,
    "$script:WinGetPackages\Ninja-build.Ninja*"
))) { $script:missingTools += "ninja" }

Resolve-FirmwareTool "STM32_Programmer_CLI" @(
    (Find-NewestBundleBin "programmer"),
    (Join-Path $env:ProgramFiles "STMicroelectronics/STM32Cube/STM32CubeProgrammer/bin")
) | Out-Null

# OpenOCD は GUI もログインも要らない経路。CubeProgrammer が無い環境でも
# 接続確認・書き込み・リセットができるので、AI から叩く既定の窓口にする。
Resolve-FirmwareTool "openocd" @(
    "$script:WinGetPackages\xpack-dev-tools.openocd-xpack*\*\bin",
    "$env:APPDATA\xPacks\openocd\*\bin",
    "$env:LOCALAPPDATA\xPacks\openocd\*\bin",
    $script:WinGetLinks
) | Out-Null
Resolve-FirmwareTool "ST-LINK_gdbserver" @(Find-NewestBundleBin "stlink-gdbserver") | Out-Null
Resolve-FirmwareTool "arm-none-eabi-gdb" @(Find-NewestBundleBin "gnu-gdb-for-stm32") | Out-Null

if (-not (Resolve-FirmwareTool "arm-none-eabi-gcc" @(
    (Find-NewestBundleBin "gnu-tools-for-stm32"),
    "$env:LOCALAPPDATA\arm-gnu-toolchain\*\bin",
    "$env:ProgramFiles\Arm GNU Toolchain arm-none-eabi\*\bin",
    "${env:ProgramFiles(x86)}\Arm GNU Toolchain arm-none-eabi\*\bin"
))) { $script:missingTools += "arm-none-eabi-gcc" }

if ($script:missingTools.Count -gt 0) {
    Write-Warning ("Missing tools: {0}. Install Arm GNU Toolchain (winget install Arm.GnuArmEmbeddedToolchain) or the STM32Cube VS Code extension bundles." -f ($script:missingTools -join ", "))
}
