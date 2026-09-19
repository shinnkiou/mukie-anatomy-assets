@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo ============================================================
echo CSMC P0.8 VTABLE / INDIRECT DISPATCH PROBE
echo ============================================================
echo.
echo This is a targeted static pass for two known loader vtables.
echo It does not modify CSMC or MODELER.
echo.
pause
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp021_RUN_VTABLE_DISPATCH.ps1"
set RC=%ERRORLEVEL%
echo.
echo Exit code: %RC%
pause
exit /b %RC%
