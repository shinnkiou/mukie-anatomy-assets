$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2.0

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PrivateRoot = "C:\Users\nurun\CSMC_ANALYSIS\PRIVATE_FULL_SNAPSHOT"
$GhidraBat = "C:\Users\nurun\CSMC_ANALYSIS\Tools\ghidra_12.1.3_PUBLIC\support\analyzeHeadless.bat"
$ModelerCopy = "C:\Users\nurun\CSMC_ANALYSIS\MODELER_COPY\CLIPStudioModeler.exe"
$ExpectedModelerSha = "2ebe2d90f8609496cb2e81a7c9defae4e851479b8e5db76eb9dd8ec05d943150"
$ProjectLocation = "C:\Users\nurun\CSMC_ANALYSIS\PRIVATE_FULL_SNAPSHOT\GHIDRA_P0_PROJECTS"
$ProjectName = "MODELER_P0_TARGETED"
$JavaScript = Join-Path $ScriptDir "02_P1_VtableDispatchMap.java"
$Classifier = Join-Path $ScriptDir "03_CLASSIFY_P1_VTABLE_MAP.py"
$Targets = Join-Path $ScriptDir "P1_TARGETS.tsv"
$Precheck = Join-Path $ScriptDir "P1_PRECHECK.txt"

foreach ($p in @($GhidraBat,$ModelerCopy,$JavaScript,$Classifier,$Targets,$Precheck)) {
    if (-not (Test-Path -LiteralPath $p)) { throw "Required file not found: $p" }
}

$ActualSha = (Get-FileHash -LiteralPath $ModelerCopy -Algorithm SHA256).Hash.ToLowerInvariant()
if ($ActualSha -ne $ExpectedModelerSha) {
    throw "MODELER_COPY SHA mismatch. Expected=$ExpectedModelerSha Actual=$ActualSha"
}

$Latest = Get-ChildItem -LiteralPath $PrivateRoot -Directory -Filter "REVIEWER_P0_*" |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $Latest) { throw "No REVIEWER_P0_* run found." }

$Reports = Join-Path $Latest.FullName "REPORTS"
$Manifest = Join-Path $Reports "decompile_manifest.tsv"
$FullRoot = Join-Path $Latest.FullName "EXTRACTED_TARGETED\FULL"
$FocusedRoot = Join-Path $Latest.FullName "EXTRACTED_TARGETED\FOCUSED"
$P08Summary = Join-Path $Reports "SUMMARY_P08.md"
foreach ($p in @($Manifest,$FullRoot,$FocusedRoot,$P08Summary)) {
    if (-not (Test-Path -LiteralPath $p)) { throw "P1 prerequisite missing: $p" }
}

$OutDir = Join-Path $Reports "P1_VTABLE_DISPATCH"
if (Test-Path -LiteralPath $OutDir) {
    $Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $Old = Join-Path $Reports ("P1_VTABLE_DISPATCH_OLD_" + $Stamp)
    Move-Item -LiteralPath $OutDir -Destination $Old
}
New-Item -ItemType Directory -Force -Path $OutDir,$ProjectLocation | Out-Null

$JavaHomeFile = "C:\Users\nurun\CSMC_ANALYSIS\JAVA21_HOME.txt"
if (Test-Path -LiteralPath $JavaHomeFile) {
    $JavaHome = (Get-Content -LiteralPath $JavaHomeFile -Raw).Trim()
    if ($JavaHome -and (Test-Path -LiteralPath $JavaHome)) {
        $env:JAVA_HOME = $JavaHome
        $env:PATH = (Join-Path $JavaHome "bin") + ";" + $env:PATH
    }
}

Write-Host "============================================================"
Write-Host "CSMC P1 - VTABLE DISPATCH MAP"
Write-Host "============================================================"
Write-Host ("Reviewer run : " + $Latest.FullName)
Write-Host ("Output       : " + $OutDir)
Write-Host ("Manifest     : " + $Manifest)
Write-Host ("MODELER SHA  : " + $ActualSha)
Write-Host ""

$ProjectFile = Join-Path $ProjectLocation ($ProjectName + ".gpr")
if (-not (Test-Path -LiteralPath $ProjectFile)) {
    Write-Host "Creating Ghidra project and importing MODELER_COPY..." -ForegroundColor Cyan
    $GArgs = @(
        $ProjectLocation,$ProjectName,
        "-import",$ModelerCopy,
        "-analysisTimeoutPerFile","1800",
        "-scriptPath",$ScriptDir,
        "-postScript","02_P1_VtableDispatchMap.java",$Targets,$Manifest,$Precheck,$OutDir,"RUN"
    )
    & $GhidraBat @GArgs
} else {
    Write-Host "Reusing existing Ghidra project..." -ForegroundColor Cyan
    $GArgs = @(
        $ProjectLocation,$ProjectName,
        "-process","CLIPStudioModeler.exe",
        "-noanalysis",
        "-scriptPath",$ScriptDir,
        "-postScript","02_P1_VtableDispatchMap.java",$Targets,$Manifest,$Precheck,$OutDir,"RUN"
    )
    & $GhidraBat @GArgs
}

$RC = $LASTEXITCODE
if ($RC -ne 0) { throw "P1 Ghidra mapper failed with exit code $RC" }

Write-Host ""
Write-Host "Running P1 classifier..." -ForegroundColor Cyan
& py -3 $Classifier --out $OutDir --manifest $Manifest --full-root $FullRoot --focused-root $FocusedRoot
$PyRC = $LASTEXITCODE
if ($PyRC -ne 0) { throw "P1 classifier failed with exit code $PyRC" }

$Packet = Join-Path $OutDir "P1_CHATGPT_PACKET.md"
$Summary = Join-Path $OutDir "P1_SUMMARY.md"
if (Test-Path -LiteralPath $Packet) {
    Copy-Item -LiteralPath $Packet -Destination (Join-Path $Reports "P1_CHATGPT_PACKET_CURRENT.md") -Force
}
if (Test-Path -LiteralPath $Summary) {
    Copy-Item -LiteralPath $Summary -Destination (Join-Path $Reports "P1_SUMMARY_CURRENT.md") -Force
}

$DriveSync = Join-Path (Split-Path -Parent $ScriptDir) "csmc_full_snapshot_reviewer_p0\04_AUTO_SYNC_GOOGLE_DRIVE.ps1"
if (Test-Path -LiteralPath $DriveSync) {
    Write-Host ""
    Write-Host "Attempting Google Drive desktop sync..." -ForegroundColor Cyan
    try {
        & powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File $DriveSync -RunRoot $Latest.FullName
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Drive sync did not complete. Local P1 reports are safe." -ForegroundColor Yellow
        }
    } catch {
        Write-Host ("Drive sync skipped: " + $_.Exception.Message) -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "============================================================"
Write-Host "P1 COMPLETE"
Write-Host "============================================================"
Write-Host ("Send/Drive file: " + $Packet)
Write-Host "Main outputs:"
Write-Host "  VTABLE_DISPATCH_MAP.tsv"
Write-Host "  P1_INTERESTING_CHAIN.tsv"
Write-Host "  P1_PRECHECK_1400452b0.txt"
Write-Host "  P1_CHATGPT_PACKET.md"
Write-Host ""
Start-Process explorer.exe $OutDir
