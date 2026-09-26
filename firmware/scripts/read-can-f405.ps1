# Live diagnostic fields, not a simultaneous snapshot. No CPU halt/reset.
[CmdletBinding()]
param([string]$Serial = '001C00363033511735393935')
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'toolchain.ps1')
$raw = & STM32_Programmer_CLI -c port=SWD "sn=$Serial" freq=100 mode=HOTPLUG -r32 0x20000000 112 2>&1
if ($LASTEXITCODE -ne 0) { throw ($raw -join "`n") }
$words = @{}
foreach ($line in $raw) {
    if ("$line" -match '^0x(200000[0-6]0)\s*:\s*(.+)$') {
        $base = [Convert]::ToUInt32($Matches[1], 16)
        $tokens = $Matches[2].Trim() -split '\s+'
        for ($j = 0; $j -lt $tokens.Count; $j++) {
            $words[[int](($base - 0x20000000) / 4) + $j] = [Convert]::ToUInt32($tokens[$j], 16)
        }
    }
}
if ($words.Count -ne 28 -or $words[0] -ne [Convert]::ToUInt32('F405CA01',16)) {
    throw 'CAN F405 diagnostics not found.'
}
[pscustomobject][ordered]@{
    phase=$words[1]; uptimeMs=$words[2]; fault=$words[3]
    loopbackOK=$words[4]; hseReady=$words[5]
    txOK=$words[6]; txFail=$words[7]; rxCount=$words[8]
    lastRawId=('0x{0:X8}' -f $words[9]); lastDlc=$words[10]
    lastLow=('0x{0:X8}' -f $words[11]); lastHigh=('0x{0:X8}' -f $words[12])
    esr=('0x{0:X8}' -f $words[13]); tec=(($words[13] -shr 16) -band 255)
    rec=(($words[13] -shr 24) -band 255); lec=(($words[13] -shr 4) -band 7)
    busOff=[bool]($words[13] -band 4); rxPin=$words[19]
    fifoOverrun=$words[20]; echoDrop=$words[21]; txRequests=$words[22]
    pathTxHigh=(($words[24] -shr 12) -band 1)
    pathRxAtHigh=(($words[24] -shr 11) -band 1)
    pathTxLow=(($words[25] -shr 12) -band 1)
    pathRxAtLow=(($words[25] -shr 11) -band 1)
    pathRxReleased=(($words[26] -shr 11) -band 1)
    pathRxWeakPulldown=(($words[27] -shr 11) -band 1)
} | ConvertTo-Json
