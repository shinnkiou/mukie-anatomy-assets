@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
set /a WAIT_COUNT=0

echo UKIE AI BRIDGE P0.18 - PAIRED CLOUD WORKER
echo This worker accepts only the P0.18 allowlist: device_status.
echo No arbitrary shell, PowerShell, EXE, or cloud filesystem path is accepted.
echo.

UKIE_AI_BRIDGE.exe worker-pair --open-browser
if errorlevel 1 goto :fail

:pair_wait
UKIE_AI_BRIDGE.exe worker-pair-status
if not errorlevel 1 goto :paired
set /a WAIT_COUNT+=1
if !WAIT_COUNT! GEQ 120 goto :pair_timeout
timeout /t 5 /nobreak >nul
goto :pair_wait

:paired
echo.
echo Pairing approved. Running one control-plane cycle now.
UKIE_AI_BRIDGE.exe worker-once
if errorlevel 1 goto :fail

echo.
echo Initial cycle completed. Starting bounded polling loop.
echo Close this window or press Ctrl+C to stop the worker.
UKIE_AI_BRIDGE.exe worker-run 10
goto :eof

:pair_timeout
echo.
echo Pairing approval timed out after 10 minutes.
echo Re-run this launcher to request a new pairing if needed.
pause
exit /b 2

:fail
echo.
echo Worker stopped because a fail-closed gate returned an error.
echo No source .blend was modified by this launcher.
pause
exit /b 2
