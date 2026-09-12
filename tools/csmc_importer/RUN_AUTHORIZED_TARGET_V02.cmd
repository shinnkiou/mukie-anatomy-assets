@echo off
setlocal EnableExtensions

rem CSMC Evidence Probe v0.2 - authorized target runner
rem Read-only. No network upload. Fails closed unless the exact known target .clip is supplied.

set "EXPECTED_SHA=ed391b6fef0f425165f6dd4719ec9000966742efde5428cb2c1446f63640e933"
set "EXPECTED_SIZE=56996715"

if "%~1"=="" goto :usage
set "TARGET=%~f1"
if not exist "%TARGET%" (
  echo [FAIL] Target file does not exist: "%TARGET%"
  exit /b 2
)

for %%F in ("%TARGET%") do set "ACTUAL_SIZE=%%~zF"
if not "%ACTUAL_SIZE%"=="%EXPECTED_SIZE%" (
  echo [FAIL] Size mismatch. Expected %EXPECTED_SIZE%, got %ACTUAL_SIZE%.
  exit /b 3
)

for /f "usebackq delims=" %%H in (`powershell -NoProfile -ExecutionPolicy Bypass -Command "(Get-FileHash -Algorithm SHA256 -LiteralPath $env:TARGET).Hash.ToLowerInvariant()"`) do set "ACTUAL_SHA=%%H"
if not defined ACTUAL_SHA (
  echo [FAIL] Could not compute SHA-256.
  exit /b 4
)
if /I not "%ACTUAL_SHA%"=="%EXPECTED_SHA%" (
  echo [FAIL] SHA-256 mismatch.
  echo Expected: %EXPECTED_SHA%
  echo Actual:   %ACTUAL_SHA%
  exit /b 5
)

set "PY_CMD="
where py >nul 2>nul && set "PY_CMD=py -3"
if not defined PY_CMD where python >nul 2>nul && set "PY_CMD=python"
if not defined PY_CMD (
  echo [FAIL] Python 3 was not found. No automatic installation is attempted.
  exit /b 6
)

set "SCRIPT=%~dp0csmc_3d_evidence_probe.py"
if not exist "%SCRIPT%" (
  echo [FAIL] Probe script is missing: "%SCRIPT%"
  exit /b 7
)

for /f "usebackq delims=" %%T in (`powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"`) do set "STAMP=%%T"
set "OUT=%~dp0PRIVATE_TARGET_RUN_%STAMP%"
set "ZIP=%~dp0PRIVATE_TARGET_RUN_%STAMP%.zip"

echo [OK] Exact authorized target identity verified.
echo [RUN] Evidence Probe v0.2

if "%~2"=="" (
  %PY_CMD% "%SCRIPT%" "%TARGET%" --outdir "%OUT%"
) else (
  set "CSMC=%~f2"
  if not exist "%~f2" (
    echo [FAIL] Optional CSMC/CS3C file does not exist: "%~f2"
    exit /b 8
  )
  %PY_CMD% "%SCRIPT%" "%TARGET%" --csmc "%~f2" --outdir "%OUT%"
)

if errorlevel 1 (
  echo [FAIL] Evidence Probe returned an error.
  exit /b 9
)

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$m=[ordered]@{runner='RUN_AUTHORIZED_TARGET_V02';target_name=[IO.Path]::GetFileName($env:TARGET);target_size=[int64]$env:ACTUAL_SIZE;target_sha256=$env:ACTUAL_SHA;probe='csmc_3d_evidence_probe_v0.2';created_utc=(Get-Date).ToUniversalTime().ToString('o');raw_input_uploaded=$false}; $m ^| ConvertTo-Json -Depth 4 ^| Set-Content -LiteralPath (Join-Path $env:OUT 'PRIVATE_RUN_MANIFEST.json') -Encoding UTF8"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "Compress-Archive -LiteralPath (Get-ChildItem -LiteralPath $env:OUT ^| ForEach-Object FullName) -DestinationPath $env:ZIP -Force"

if not exist "%ZIP%" (
  echo [WARN] Reports were created but ZIP packaging failed.
  echo Output: "%OUT%"
  exit /b 10
)

echo.
echo [PASS] Private target probe completed.
echo Reports: "%OUT%"
echo Bundle:  "%ZIP%"
echo The input .clip was read only and was not copied into the report bundle.
exit /b 0

:usage
echo Usage:
echo   Drag the authorized target .clip onto this CMD
echo or:
echo   RUN_AUTHORIZED_TARGET_V02.cmd "target.clip" ["optional.csmc"]
echo.
echo This runner accepts only the known authorized target SHA-256 and size.
exit /b 1
