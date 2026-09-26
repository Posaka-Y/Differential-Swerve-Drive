<# Read live AMT102 bring-up diagnostics through SWD without stopping the CPU.
   Each 32-bit field is live; fields/channels are NOT a simultaneous snapshot. #>
[CmdletBinding()]
param(
    [ValidatePattern('^[a-zA-Z0-9_-]+$')]
    [string]$Serial = '001C00363033511735393935',
    [ValidateRange(1, 120)][int]$Samples = 1,
    [ValidateRange(50, 5000)][int]$IntervalMs = 500
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'toolchain.ps1')
for ($sample = 0; $sample -lt $Samples; $sample++) {
    $raw = & STM32_Programmer_CLI -c port=SWD "sn=$Serial" freq=100 mode=HOTPLUG -r32 0x20000000 64 2>&1
    if ($LASTEXITCODE -ne 0) { throw ($raw -join "`n") }
    $words = @{}
    foreach ($line in $raw) {
        if ("$line" -match '^0x(200000[0-3]0)\s*:\s*(.+)$') {
            $base = [Convert]::ToUInt32($Matches[1], 16)
            $tokens = $Matches[2].Trim() -split '\s+'
            for ($j = 0; $j -lt $tokens.Count; $j++) {
                $words[[int](($base - 0x20000000) / 4) + $j] = [Convert]::ToUInt32($tokens[$j], 16)
            }
        }
    }
    if ($words.Count -ne 16 -or $words[0] -ne [Convert]::ToUInt32('F405A102',16)) {
        throw 'AMT102 firmware diagnostics not found. Check the flashed image.'
    }
    if ($words[3] -ne 0) { throw ('MCU fault: 0x{0:X8}' -f $words[3]) }
    $result = [ordered]@{ time = (Get-Date).ToString('HH:mm:ss.fff'); uptimeMs = $words[2] }
    for ($i = 0; $i -lt 3; $i++) {
        $count = [long]$words[7 + $i]
        if ($count -ge 2147483648L) { $count -= 4294967296L }
        $prefix = 'J' + (4 + $i)
        $result[$prefix + '_count'] = $count
        $result[$prefix + '_AB'] = [Convert]::ToString($words[10 + $i], 2).PadLeft(2, '0')
        $result[$prefix + '_changes'] = $words[13 + $i]
    }
    [pscustomobject]$result | ConvertTo-Json -Compress
    if ($sample + 1 -lt $Samples) { Start-Sleep -Milliseconds $IntervalMs }
}
