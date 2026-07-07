[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [scriptblock]$Body,

    [Parameter(Mandatory)]
    [scriptblock]$SafeIdle,

    [string]$Owner = "unspecified",

    [string]$MutexName = "Global\DifferentialSwerveHardwareSession"
)

$startedAt = [DateTimeOffset]::Now
$mutex = $null
$acquired = $false
$safeIdleSucceeded = $false
$released = $false
$bodyResult = $null
$safeIdleResult = $null
$bodyError = $null
$safeIdleError = $null
$lockError = $null
$releaseError = $null

try {
    $mutex = [System.Threading.Mutex]::new($false, $MutexName)
    try {
        $acquired = $mutex.WaitOne(0)
    }
    catch [System.Threading.AbandonedMutexException] {
        # The previous owner exited without releasing the mutex. Ownership is
        # transferred to this process, so the session may proceed safely.
        $acquired = $true
    }

    if ($acquired) {
        try {
            $bodyResult = & $Body
        }
        catch {
            $bodyError = $_.Exception.Message
        }
    }
}
catch {
    $lockError = $_.Exception.Message
}
finally {
    if ($acquired) {
        try {
            $safeIdleResult = & $SafeIdle
            $safeIdleSucceeded = $true
        }
        catch {
            $safeIdleError = $_.Exception.Message
        }

        if ($safeIdleSucceeded) {
            try {
                $mutex.ReleaseMutex()
                $released = $true
            }
            catch {
                $releaseError = $_.Exception.Message
            }
            finally {
                $mutex.Dispose()
            }
        }
        else {
            # Deliberately retain ownership for the lifetime of this PowerShell
            # process. A caller must not start another hardware session after a
            # failed safe-idle handoff.
            $script:DifferentialSwerveFailedHardwareSessionMutex = $mutex
        }
    }
    elseif ($null -ne $mutex) {
        $mutex.Dispose()
    }
}

$status = if ($lockError) {
    "lock_error"
}
elseif (-not $acquired) {
    "busy"
}
elseif (-not $safeIdleSucceeded) {
    "safe_idle_failed"
}
elseif ($releaseError) {
    "release_failed"
}
elseif ($bodyError) {
    "body_failed_safe_idle_ok"
}
else {
    "completed_safe_idle_ok"
}

[pscustomobject]@{
    Status            = $status
    Owner             = $Owner
    MutexName         = $MutexName
    Acquired          = $acquired
    BodySucceeded     = $acquired -and ($null -eq $bodyError)
    SafeIdleSucceeded = $safeIdleSucceeded
    Released          = $released
    BodyResult        = $bodyResult
    SafeIdleResult    = $safeIdleResult
    BodyError         = $bodyError
    SafeIdleError     = $safeIdleError
    LockError         = $lockError
    ReleaseError      = $releaseError
    StartedAt         = $startedAt.ToString("o")
    FinishedAt        = [DateTimeOffset]::Now.ToString("o")
}
