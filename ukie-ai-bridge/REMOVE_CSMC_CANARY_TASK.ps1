$ErrorActionPreference = 'Stop'

# Fixed, parameterless rollback for the isolated CSMC canary Scheduled Task.
# It removes only the fixed LIMITED task and the fixed canary install directory.
# It does not touch the production Worker executable, credential, pairing state,
# production Scheduled Tasks, registry, services, or arbitrary filesystem paths.

$TaskName = 'UKIE_CSMC_CANARY'
$CanaryRoot = Join-Path $env:LOCALAPPDATA 'UKIE_AI_BRIDGE\csmc-canary'
$InstallRoot = Join-Path $CanaryRoot 'current'
$Schtasks = Join-Path $env:SystemRoot 'System32\schtasks.exe'

if (-not $env:LOCALAPPDATA) { throw 'LOCALAPPDATA is unavailable.' }
if (-not (Test-Path -LiteralPath $Schtasks -PathType Leaf)) { throw 'Fixed schtasks.exe path is unavailable.' }

# Delete only the exact canary task. A missing task is treated as already removed.
& $Schtasks /Query /TN $TaskName *> $null
$TaskExists = ($LASTEXITCODE -eq 0)
if ($TaskExists) {
  & $Schtasks /Delete /TN $TaskName /F | Out-Null
  if ($LASTEXITCODE -ne 0) { throw "Failed to delete fixed CSMC canary task; exit code $LASTEXITCODE" }
}

# Guard the fixed delete root against accidental broadening.
$ExpectedRoot = [IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA 'UKIE_AI_BRIDGE\csmc-canary'))
$ActualRoot = [IO.Path]::GetFullPath($CanaryRoot)
if (-not [string]::Equals($ExpectedRoot.TrimEnd('\'), $ActualRoot.TrimEnd('\'), [StringComparison]::OrdinalIgnoreCase)) {
  throw 'Canary rollback root guard failed.'
}
if (Test-Path -LiteralPath $InstallRoot) {
  Remove-Item -LiteralPath $InstallRoot -Recurse -Force
}

[ordered]@{
  status = 'REMOVED'
  task_name = $TaskName
  task_existed = $TaskExists
  install_root = $InstallRoot
  production_worker_changed = $false
  production_pairing_changed = $false
  registry_changed = $false
  service_changed = $false
  admin_required = $false
} | ConvertTo-Json -Depth 4
