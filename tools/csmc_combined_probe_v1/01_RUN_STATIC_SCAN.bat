@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title CSMC Combined Static Scan V1

echo ============================================================
echo  CSMC COMBINED STATIC SCAN V1
echo ============================================================
echo.
echo Read-only scan. It does not modify the CSMC.
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp002_STATIC_SCAN.ps1" %*
set RC=%ERRORLEVEL%

echo.
if not "%RC%"=="0" echo [FAILED] Exit code %RC%
pause
exit /b %RC%
