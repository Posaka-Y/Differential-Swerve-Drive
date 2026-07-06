[CmdletBinding()]
param(
    [ValidateSet("Debug", "Release")]
    [string]$Configuration = "Debug",
    [switch]$NoBuild
)

$ErrorActionPreference = "Stop"
$firmwareRoot = Split-Path -Parent $PSScriptRoot
$preset = $Configuration.ToLowerInvariant()

. (Join-Path $PSScriptRoot "toolchain.ps1")

if (-not $NoBuild) {
    & (Join-Path $PSScriptRoot "build.ps1") -Configuration $Configuration
}

$image = Join-Path $firmwareRoot "build/$preset/differential_swerve_firmware.hex"
if (-not (Test-Path -LiteralPath $image)) { throw "Firmware image not found: $image" }

$programmer = Get-Command "STM32_Programmer_CLI" -ErrorAction SilentlyContinue
if (-not $programmer) {
    $defaultPath = Join-Path $env:ProgramFiles "STMicroelectronics/STM32Cube/STM32CubeProgrammer/bin/STM32_Programmer_CLI.exe"
    if (-not (Test-Path -LiteralPath $defaultPath)) {
        throw "STM32_Programmer_CLI was not found. Add STM32CubeProgrammer/bin to PATH."
    }
    $programmerPath = $defaultPath
}
else {
    $programmerPath = $programmer.Source
}

& $programmerPath -c port=SWD -w $image -v -rst
if ($LASTEXITCODE -ne 0) { throw "Programming failed." }
