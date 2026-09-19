$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2.0

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PrivateRoot = "C:\Users\nurun\CSMC_ANALYSIS\PRIVATE_FULL_SNAPSHOT"
$GhidraBat = "C:\Users\nurun\CSMC_ANALYSIS\Tools\ghidra_12.1.3_PUBLIC\support\analyzeHeadless.bat"
$ModelerCopy = "C:\Users\nurun\CSMC_ANALYSIS\MODELER_COPY\CLIPStudioModeler.exe"
$ExpectedModelerSha = "2ebe2d90f8609496cb2e81a7c9defae4e851479b8e5db76eb9dd8ec05d943150"
$ProjectLocation = "C:\Users\nurun\CSMC_ANALYSIS\PRIVATE_FULL_SNAPSHOT\GHIDRA_P0_PROJECTS"
$ProjectName = "MODELER_P0_TARGETED"
$PostScript = "22_VtableDispatchProbe.java"
$TargetsFile = Join-Path $ScriptDir "VTABLE_TARGETS.txt"

foreach ($p in @($GhidraBat, $ModelerCopy, $TargetsFile, (Join-Path $ScriptDir $PostScript))) {
    if (-not (Test-Path -LiteralPath $p)) { throw "Required file not found: $p" }
}

$ActualSha = (Get-FileHash -LiteralPath $ModelerCopy -Algorithm SHA256).Hash.ToLowerInvariant()
if ($ActualSha -ne $ExpectedModelerSha) {
    throw "MODELER_COPY SHA mismatch. Expected=$ExpectedModelerSha Actual=$ActualSha"
}

$Latest = Get-ChildItem -LiteralPath $PrivateRoot -Directory -Filter "REVIEWER_P0_*" |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $Latest) { throw "No REVIEWER_P0_* run found." }

$P08Summary = Join-Path (Join-Path $Latest.FullName "REPORTS") "SUMMARY_P08.md"
if (-not (Test-Path -LiteralPath $P08Summary)) {
    throw "Safety gate: latest reviewer run is not P0.8. Run 00_START_HERE.cmd with P0.8 first."
}

$Reports = Join-Path $Latest.FullName "REPORTS"
$OutDir = Join-Path $Reports "VTABLE_DISPATCH"
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
Write-Host "P0.8 targeted vtable/indirect-dispatch pass"
Write-Host ("Latest reviewer: " + $Latest.FullName)
Write-Host ("Output         : " + $OutDir)
Write-Host ("MODELER SHA256 : " + $ActualSha)

if (-not (Test-Path -LiteralPath $ProjectFile)) {
    Write-Host "Creating Ghidra project and importing MODELER_COPY..." -ForegroundColor Cyan
    $Args = @(
        $ProjectLocation, $ProjectName,
        "-import", $ModelerCopy,
        "-analysisTimeoutPerFile", "1800",
        "-scriptPath", $ScriptDir,
        "-postScript", $PostScript, $TargetsFile, $OutDir
    )
    & $GhidraBat @Args
} else {
    Write-Host "Reusing Ghidra project..." -ForegroundColor Cyan
    $Args = @(
        $ProjectLocation, $ProjectName,
        "-process", "CLIPStudioModeler.exe",
        "-noanalysis",
        "-scriptPath", $ScriptDir,
        "-postScript", $PostScript, $TargetsFile, $OutDir
    )
    & $GhidraBat @Args
}

$RC = $LASTEXITCODE
if ($RC -ne 0) { throw "Vtable dispatch Ghidra pass failed with exit code $RC" }
Write-Host "Vtable/indirect-dispatch pass complete." -ForegroundColor Green
Start-Process explorer.exe $OutDir
