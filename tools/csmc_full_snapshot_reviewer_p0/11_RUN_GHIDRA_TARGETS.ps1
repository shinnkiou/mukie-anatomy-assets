$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2.0

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PrivateRoot = "C:\Users\nurun\CSMC_ANALYSIS\PRIVATE_FULL_SNAPSHOT"
$GhidraBat = "C:\Users\nurun\CSMC_ANALYSIS\Tools\ghidra_12.1.3_PUBLIC\support\analyzeHeadless.bat"
$ModelerCopy = "C:\Users\nurun\CSMC_ANALYSIS\MODELER_COPY\CLIPStudioModeler.exe"
$ExpectedModelerSha = "2ebe2d90f8609496cb2e81a7c9defae4e851479b8e5db76eb9dd8ec05d943150"
$ProjectLocation = "C:\Users\nurun\CSMC_ANALYSIS\PRIVATE_FULL_SNAPSHOT\GHIDRA_P0_PROJECTS"
$ProjectName = "MODELER_P0_TARGETED"
$PostScript = "12_TargetedRvaDecompile.java"

if (-not (Test-Path -LiteralPath $GhidraBat)) {
    throw "Ghidra analyzeHeadless.bat not found: $GhidraBat"
}
if (-not (Test-Path -LiteralPath $ModelerCopy)) {
    throw "MODELER_COPY not found: $ModelerCopy"
}

$ActualSha = (Get-FileHash -LiteralPath $ModelerCopy -Algorithm SHA256).Hash.ToLowerInvariant()
if ($ActualSha -ne $ExpectedModelerSha) {
    throw "MODELER_COPY SHA mismatch. Expected=$ExpectedModelerSha Actual=$ActualSha"
}

$Latest = Get-ChildItem -LiteralPath $PrivateRoot -Directory -Filter "REVIEWER_P0_*" |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if (-not $Latest) {
    throw "No REVIEWER_P0_* run found."
}

$Reports = Join-Path $Latest.FullName "REPORTS"
$Targets = Join-Path $Reports "ghidra_targets.txt"
if (-not (Test-Path -LiteralPath $Targets)) {
    throw "ghidra_targets.txt not found: $Targets"
}

$AllTargetText = Get-Content -LiteralPath $Targets
if (-not ($AllTargetText -match "reviewer_build=P0.7_direct_evidence")) {
    throw "Safety gate: ghidra_targets.txt is not from P0.7 direct-evidence reviewer. Run 00_START_HERE.cmd with P0.7 first."
}

$TargetLines = @(
    $AllTargetText |
        Where-Object { $_ -and (-not $_.StartsWith("#")) }
)

if ($TargetLines.Count -eq 0) {
    Write-Host "No new Ghidra targets. Exiting without broad analysis." -ForegroundColor Yellow
    exit 0
}
if ($TargetLines.Count -gt 8) {
    throw "Safety gate: target count > 8. Refusing broad analysis."
}

$OutDir = Join-Path $Reports "GHIDRA_TARGETED"
New-Item -ItemType Directory -Force -Path $OutDir, $ProjectLocation | Out-Null

$JavaHomeFile = "C:\Users\nurun\CSMC_ANALYSIS\JAVA21_HOME.txt"
if (Test-Path -LiteralPath $JavaHomeFile) {
    $JavaHome = (Get-Content -LiteralPath $JavaHomeFile -Raw).Trim()
    if ($JavaHome -and (Test-Path -LiteralPath $JavaHome)) {
        $env:JAVA_HOME = $JavaHome
        $env:PATH = (Join-Path $JavaHome "bin") + ";" + $env:PATH
    }
}

$ProjectFile = Join-Path $ProjectLocation ($ProjectName + ".gpr")

Write-Host ("Latest reviewer: " + $Latest.FullName)
Write-Host ("Targets        : " + $TargetLines.Count)
Write-Host ("Ghidra output  : " + $OutDir)
Write-Host ("MODELER SHA256 : " + $ActualSha)

if (-not (Test-Path -LiteralPath $ProjectFile)) {
    Write-Host "Creating dedicated Ghidra project and importing MODELER_COPY..." -ForegroundColor Cyan
    $Args = @(
        $ProjectLocation,
        $ProjectName,
        "-import", $ModelerCopy,
        "-analysisTimeoutPerFile", "1800",
        "-scriptPath", $ScriptDir,
        "-postScript", $PostScript, $Targets, $OutDir
    )
    & $GhidraBat @Args
} else {
    Write-Host "Reusing dedicated Ghidra project..." -ForegroundColor Cyan
    $Args = @(
        $ProjectLocation,
        $ProjectName,
        "-process", "CLIPStudioModeler.exe",
        "-noanalysis",
        "-scriptPath", $ScriptDir,
        "-postScript", $PostScript, $Targets, $OutDir
    )
    & $GhidraBat @Args
}

$RC = $LASTEXITCODE
if ($RC -ne 0) {
    throw "Ghidra targeted pass failed with exit code $RC"
}

Write-Host "Ghidra targeted pass complete." -ForegroundColor Green
Start-Process explorer.exe $OutDir
