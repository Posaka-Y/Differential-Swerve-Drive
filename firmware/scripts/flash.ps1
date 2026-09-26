[CmdletBinding()]
param(
    [ValidateSet("Debug", "Release")]
    [string]$Configuration = "Debug",
    [switch]$NoBuild,

    # 書き込み手段。auto は openocd -> STM32_Programmer_CLI の順に探す。
    [ValidateSet("auto", "openocd", "cubeprogrammer")]
    [string]$Tool = "auto",

    # 対象MCU系列 (openocd 使用時のみ)。unit board=stm32g4x、ODOM board=stm32f4x。
    [ValidateSet("stm32g4x", "stm32f4x")]
    [string]$Target = "stm32g4x"
)

$ErrorActionPreference = "Stop"
if ($Target -ne 'stm32g4x') {
    throw 'Current build artifacts are STM32G4 firmware. Refusing to flash them to STM32F4; an F405-specific build is required.'
}
$firmwareRoot = Split-Path -Parent $PSScriptRoot
$preset = $Configuration.ToLowerInvariant()

. (Join-Path $PSScriptRoot "toolchain.ps1")

if (-not $NoBuild) {
    & (Join-Path $PSScriptRoot "build.ps1") -Configuration $Configuration
}

$image = Join-Path $firmwareRoot "build/$preset/differential_swerve_firmware.hex"
if (-not (Test-Path -LiteralPath $image)) { throw "Firmware image not found: $image" }

$openocd = Get-Command "openocd" -ErrorAction SilentlyContinue
$programmer = Get-Command "STM32_Programmer_CLI" -ErrorAction SilentlyContinue
if (-not $programmer) {
    $defaultPath = Join-Path $env:ProgramFiles "STMicroelectronics/STM32Cube/STM32CubeProgrammer/bin/STM32_Programmer_CLI.exe"
    if (Test-Path -LiteralPath $defaultPath) {
        $programmer = [PSCustomObject]@{ Source = $defaultPath }
    }
}

$selected = switch ($Tool) {
    "openocd" {
        if (-not $openocd) { throw "openocd was not found. Run firmware/scripts/setup-windows.ps1." }
        "openocd"
    }
    "cubeprogrammer" {
        if (-not $programmer) { throw "STM32_Programmer_CLI was not found. Add STM32CubeProgrammer/bin to PATH." }
        "cubeprogrammer"
    }
    default {
        if ($openocd) { "openocd" }
        elseif ($programmer) { "cubeprogrammer" }
        else { throw "No programmer found. Run firmware/scripts/setup-windows.ps1, or add STM32CubeProgrammer/bin to PATH." }
    }
}

Write-Host "Programming with $selected : $image" -ForegroundColor Cyan

if ($selected -eq "openocd") {
    $scriptsDir = Resolve-OpenOcdScriptsDir -OpenOcdPath $openocd.Source
    # TCL 側はバックスラッシュをエスケープとして解釈するため、必ず / に直す。
    $imageForTcl = ($image -replace '\\', '/')

    $arguments = @()
    if ($scriptsDir) { $arguments += @("-s", $scriptsDir) }
    $arguments += @(
        "-f", "interface/stlink.cfg",
        "-f", "target/$Target.cfg",
        "-c", "program `"$imageForTcl`" verify reset exit"
    )
    & $openocd.Source @arguments
    if ($LASTEXITCODE -ne 0) { throw "Programming failed (openocd exit $LASTEXITCODE)." }
}
else {
    & $programmer.Source -c port=SWD -w $image -v -rst
    if ($LASTEXITCODE -ne 0) { throw "Programming failed." }
}

Write-Host "Done. Verify with: .\firmware\scripts\probe.ps1 -Target $Target" -ForegroundColor Green
