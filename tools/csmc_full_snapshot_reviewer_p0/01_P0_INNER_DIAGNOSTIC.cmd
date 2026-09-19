@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ============================================================
echo CSMC FULL SNAPSHOT REVIEWER P0 - INNER DIAGNOSTIC
echo ============================================================
echo.
echo This window is intentionally persistent.
echo Script directory:
echo   %CD%
echo.

set "ROOT=C:\Users\nurun\CSMC_ANALYSIS\PRIVATE_FULL_SNAPSHOT"
set "LOG=%ROOT%\REVIEWER_P0_DIAGNOSTIC.log"

if not exist "%ROOT%" mkdir "%ROOT%" >nul 2>&1

echo Started: %DATE% %TIME% > "%LOG%"
echo ScriptDir: %CD% >> "%LOG%"

echo Checking required files...
echo.

if not exist "%~dp001_RUN_REVIEWER_P0.ps1" (
  echo [FAIL] Missing 01_RUN_REVIEWER_P0.ps1
  echo [FAIL] Missing 01_RUN_REVIEWER_P0.ps1 >> "%LOG%"
  goto HOLD
)
echo [PASS] 01_RUN_REVIEWER_P0.ps1

if not exist "%~dp002_ANALYZE_TARGETED_SNAPSHOT.py" (
  echo [FAIL] Missing 02_ANALYZE_TARGETED_SNAPSHOT.py
  echo [FAIL] Missing 02_ANALYZE_TARGETED_SNAPSHOT.py >> "%LOG%"
  goto HOLD
)
echo [PASS] 02_ANALYZE_TARGETED_SNAPSHOT.py

if not exist "%~dp0KNOWN_FACTS.json" (
  echo [FAIL] Missing KNOWN_FACTS.json
  echo [FAIL] Missing KNOWN_FACTS.json >> "%LOG%"
  goto HOLD
)
echo [PASS] KNOWN_FACTS.json

echo.
echo Checking snapshot files...
set "S1=C:\Users\nurun\CSMC_ANALYSIS\PRIVATE_FULL_SNAPSHOT\CSMC_FULL_SNAPSHOT_20260914_214659.zip"
set "S2=C:\Users\nurun\CSMC_ANALYSIS\PRIVATE_FULL_SNAPSHOT\CSMC_FULL_SNAPSHOT_FOCUSED_20260914_232435.zip"

if exist "%S1%" (
  echo [PASS] FULL snapshot found
) else (
  echo [WARN] FULL snapshot missing:
  echo        %S1%
)

if exist "%S2%" (
  echo [PASS] FOCUSED snapshot found
) else (
  echo [WARN] FOCUSED snapshot missing:
  echo        %S2%
)

echo.
echo Press any key to start PowerShell reviewer.
pause >nul

echo.
echo Running PowerShell...
echo ------------------------------------------------------------
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp001_RUN_REVIEWER_P0.ps1" 1>>"%LOG%" 2>&1
set "RC=%ERRORLEVEL%"
echo ------------------------------------------------------------
echo.
echo PowerShell exit code: %RC%
echo PowerShell exit code: %RC% >> "%LOG%"

echo.
echo Last 80 log lines:
echo ============================================================
powershell.exe -NoLogo -NoProfile -Command "if (Test-Path -LiteralPath '%LOG%') { Get-Content -LiteralPath '%LOG%' -Tail 80 }"
echo ============================================================
echo.

:HOLD
echo This window will NOT close automatically.
echo Diagnostic log:
echo   %LOG%
echo.
echo Send a screenshot of this window or the diagnostic log to ChatGPT.
echo.
echo Type EXIT only when you want to close this window.
cmd /k
