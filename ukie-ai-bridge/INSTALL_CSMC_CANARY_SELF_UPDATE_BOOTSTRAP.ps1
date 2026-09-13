$ErrorActionPreference = 'Stop'

# One-time installer for the fixed isolated CSMC canary self-update bootstrap.
# It does not alter Production Worker files, pairing, registry, services, or any
# path outside %LOCALAPPDATA%\UKIE_AI_BRIDGE\csmc-canary and the one fixed task.
$TaskName = 'UKIE_CSMC_CANARY'
$CanaryRoot = Join-Path $env:LOCALAPPDATA 'UKIE_AI_BRIDGE\csmc-canary'
$BootstrapRoot = Join-Path $CanaryRoot 'bootstrap'
$SourceRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ManifestPath = Join-Path $SourceRoot 'BOOTSTRAP_MANIFEST.json'
$BootstrapExeName = 'CSMC_CANARY_SELF_UPDATE.exe'
$Schtasks = Join-Path $env:SystemRoot 'System32\schtasks.exe'

if (-not $env:LOCALAPPDATA) { throw 'LOCALAPPDATA is unavailable.' }
if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) { throw 'BOOTSTRAP_MANIFEST.json is missing.' }
if (-not (Test-Path -LiteralPath $Schtasks -PathType Leaf)) { throw 'Fixed schtasks.exe path is unavailable.' }
$Manifest = Get-Content -Raw -LiteralPath $ManifestPath | ConvertFrom-Json
if ([string]$Manifest.schema_version -ne 'csmc_canary_self_update_bootstrap_manifest_v1') { throw 'Bootstrap manifest schema mismatch.' }
if ([int]$Manifest.bootstrap_version -ne 1) { throw 'Bootstrap version mismatch.' }

function Assert-Hash([string]$Root,[string]$Name){
  $Entry=$Manifest.files|Where-Object{$_.name-eq$Name}
  if($null-eq$Entry-or@($Entry).Count-ne1){throw "Bootstrap manifest entry invalid: $Name"}
  $Path=Join-Path $Root $Name
  if(-not(Test-Path -LiteralPath $Path -PathType Leaf)){throw "Bootstrap file missing: $Name"}
  if((Get-Item -LiteralPath $Path).Length-ne[int64]$Entry.size){throw "Bootstrap size mismatch: $Name"}
  $Actual=(Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()
  if($Actual-ne([string]$Entry.sha256).ToLowerInvariant()){throw "Bootstrap SHA-256 mismatch: $Name"}
}

Assert-Hash $SourceRoot $BootstrapExeName
New-Item -ItemType Directory -Force -Path $BootstrapRoot|Out-Null
Copy-Item -LiteralPath (Join-Path $SourceRoot $BootstrapExeName) -Destination (Join-Path $BootstrapRoot $BootstrapExeName) -Force
Copy-Item -LiteralPath $ManifestPath -Destination (Join-Path $BootstrapRoot 'BOOTSTRAP_MANIFEST.json') -Force
Assert-Hash $BootstrapRoot $BootstrapExeName

$BootstrapExe=Join-Path $BootstrapRoot $BootstrapExeName
& $BootstrapExe self-test | Out-Host
if($LASTEXITCODE-ne0){throw "bootstrap self-test failed with exit code $LASTEXITCODE"}

# The existing fixed task is repointed once from the versioned canary worker to
# the immutable bootstrap. The bootstrap itself then runs the active current
# worker after checking the fixed promoted release endpoint.
$TaskRun='"'+$BootstrapExe+'"'
& $Schtasks /Create /TN $TaskName /TR $TaskRun /SC MINUTE /MO 5 /RL LIMITED /F | Out-Null
if($LASTEXITCODE-ne0){throw "schtasks.exe failed with exit code $LASTEXITCODE"}

[ordered]@{
  status='SELF_UPDATE_BOOTSTRAP_INSTALLED'
  bootstrap_version=1
  task_name=$TaskName
  task_target='CSMC_CANARY_SELF_UPDATE.exe'
  canary_root=$CanaryRoot
  bootstrap_root=$BootstrapRoot
  cadence_minutes=5
  run_level='LIMITED'
  release_endpoint='FIXED_BASE44_CSMC_CANARY_RELEASE_ONLY'
  production_worker_changed=$false
  arbitrary_url=$false
  arbitrary_path=$false
  arbitrary_command=$false
  admin_required=$false
  registry_changed=$false
}|ConvertTo-Json -Depth 5
