$ErrorActionPreference = 'Stop'

# Fixed, parameterless installer for isolated CSMC canary v4.
# Copies only manifest-pinned files to one LOCALAPPDATA root and creates one
# LIMITED task that runs exactly `UKIE_AI_BRIDGE_CSMC_CANARY.exe once`.
$TaskName = 'UKIE_CSMC_CANARY'
$InstallRoot = Join-Path $env:LOCALAPPDATA 'UKIE_AI_BRIDGE\csmc-canary\current'
$ArtifactRoot = Join-Path $env:LOCALAPPDATA 'UKIE_AI_BRIDGE\csmc-canary\artifacts'
$SourceRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ManifestPath = Join-Path $SourceRoot 'PACKAGE_MANIFEST.json'
$Schtasks = Join-Path $env:SystemRoot 'System32\schtasks.exe'

if (-not $env:LOCALAPPDATA) { throw 'LOCALAPPDATA is unavailable.' }
if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) { throw 'PACKAGE_MANIFEST.json is missing.' }
if (-not (Test-Path -LiteralPath $Schtasks -PathType Leaf)) { throw 'Fixed schtasks.exe path is unavailable.' }
$Manifest = Get-Content -Raw -LiteralPath $ManifestPath | ConvertFrom-Json
$Required = @(
  'UKIE_AI_BRIDGE_CSMC_CANARY.exe',
  'BP3D_ModelerObserver_P4_1.ps1',
  'BP3D_ModelerObserver_P4_1_DIAG_V1.ps1',
  'CSMC_AutoCycle_V01.py',
  'RELEASE_INFO.json'
)
function Assert-Hash([string]$Root,[string]$Name){
  $Entry=$Manifest.files|Where-Object{$_.name-eq$Name}
  if($null-eq$Entry-or@($Entry).Count-ne1){throw "Manifest entry invalid: $Name"}
  $Path=Join-Path $Root $Name
  if(-not(Test-Path -LiteralPath $Path -PathType Leaf)){throw "Required package file missing: $Name"}
  $Actual=(Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToLowerInvariant()
  if($Actual-ne([string]$Entry.sha256).ToLowerInvariant()){throw "SHA-256 mismatch: $Name"}
}
foreach($Name in $Required){Assert-Hash $SourceRoot $Name}
New-Item -ItemType Directory -Force -Path $InstallRoot,$ArtifactRoot|Out-Null
foreach($Name in $Required){Copy-Item -LiteralPath (Join-Path $SourceRoot $Name) -Destination (Join-Path $InstallRoot $Name) -Force}
Copy-Item -LiteralPath $ManifestPath -Destination (Join-Path $InstallRoot 'PACKAGE_MANIFEST.json') -Force
foreach($Name in $Required){Assert-Hash $InstallRoot $Name}
$Worker=Join-Path $InstallRoot 'UKIE_AI_BRIDGE_CSMC_CANARY.exe'
$TaskRun='"'+$Worker+'" once'
& $Schtasks /Create /TN $TaskName /TR $TaskRun /SC MINUTE /MO 5 /RL LIMITED /F | Out-Null
if($LASTEXITCODE-ne0){throw "schtasks.exe failed with exit code $LASTEXITCODE"}
[ordered]@{
  status='INSTALLED'; package='CSMC_CANARY_V4'; task_name=$TaskName; install_root=$InstallRoot; artifact_root=$ArtifactRoot
  cadence_minutes=5; run_level='LIMITED'; worker_command='UKIE_AI_BRIDGE_CSMC_CANARY.exe once'
  capabilities=@('csmc_observer_capture','csmc_observer_diagnose_v1','csmc_artifact_upload')
  arbitrary_command=$false; arbitrary_url=$false; admin_required=$false; registry_changed=$false; local_original_delete=$false
}|ConvertTo-Json -Depth 5
