$ErrorActionPreference = 'Stop'
$tokens = $null
$errors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile(
    (Join-Path $PSScriptRoot 'probe.ps1'), [ref]$tokens, [ref]$errors)
if ($errors.Count) { throw ($errors | Out-String) }
$function = $ast.Find({ param($node)
    $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and
    $node.Name -eq 'Invoke-WithTimeout'
}, $true)
. ([scriptblock]::Create($function.Extent.Text))
$shell = (Get-Process -Id $PID).Path
$run = Invoke-WithTimeout -FilePath $shell -Arguments @(
    '-NoProfile', '-Command', '[Console]::WriteLine(''C:\path with spaces\日本語\''); [Console]::Error.WriteLine(''stderr quoted "text"''); exit 7'
) -Seconds 10
if ($run.timedOut -or $run.exitCode -ne 7 -or
    -not $run.output.Contains('C:\path with spaces\日本語\') -or
    -not $run.output.Contains('stderr quoted "text"')) { throw ($run | ConvertTo-Json) }
$run = Invoke-WithTimeout -FilePath $shell -Arguments @('-NoProfile', '-Command', 'Start-Sleep -Seconds 20') -Seconds 1
if (-not $run.timedOut) { throw 'Timeout was not enforced' }
Write-Output 'PASS: arguments (spaces, Unicode, quotes, backslashes), stderr, exit code, timeout'
