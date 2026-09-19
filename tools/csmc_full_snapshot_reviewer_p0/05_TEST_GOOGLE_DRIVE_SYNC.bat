@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo ============================================================
echo CSMC GOOGLE DRIVE SYNC TEST
echo ============================================================
echo.
echo This test only copies the latest REPORTS folder to the
echo Google Drive desktop sync folder. It does not touch CSMC.
echo.
set "ROOT=C:\Users\nurun\CSMC_ANALYSIS\PRIVATE_FULL_SNAPSHOT"
for /f "delims=" %%D in ('dir /b /ad /o-d "%ROOT%\REVIEWER_P0_*" 2^>nul') do (
  set "LATEST=%ROOT%\%%D"
  goto FOUND
)
:FOUND
if not defined LATEST (
  echo No REVIEWER_P0_* folder found.
  pause
  exit /b 1
)
echo Latest: %LATEST%
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp004_AUTO_SYNC_GOOGLE_DRIVE.ps1" -RunRoot "%LATEST%"
set RC=%ERRORLEVEL%
echo Exit code: %RC%
pause
exit /b %RC%
