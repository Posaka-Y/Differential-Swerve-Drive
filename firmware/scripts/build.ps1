[CmdletBinding()]
param(
    [ValidateSet("Debug", "Release")]
    [string]$Configuration = "Debug",
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
$firmwareRoot = Split-Path -Parent $PSScriptRoot
$preset = $Configuration.ToLowerInvariant()

. (Join-Path $PSScriptRoot "toolchain.ps1")

Push-Location $firmwareRoot
try {
    if ($Clean) {
        $buildDirectory = Join-Path $firmwareRoot "build/$preset"
        if (Test-Path -LiteralPath $buildDirectory) {
            Remove-Item -LiteralPath $buildDirectory -Recurse -Force
        }
    }
    cmake --preset $preset
    if ($LASTEXITCODE -ne 0) { throw "CMake configure failed." }
    cmake --build --preset $preset
    if ($LASTEXITCODE -ne 0) { throw "Firmware build failed." }
    Write-Host "Output: $firmwareRoot/build/$preset/differential_swerve_firmware.elf"
}
finally {
    Pop-Location
}
