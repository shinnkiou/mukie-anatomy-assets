@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title CSMC Runtime VBO Caller Probe V1

echo ============================================================
echo  CSMC RUNTIME VBO CALLER PROBE V1
echo ============================================================
echo.
echo Close CLIP STUDIO MODELER before continuing.
echo.
pause

py -3 -c "import frida" >nul 2>&1
if not errorlevel 1 (
  py -3 "%~dp004_RUNTIME_PROBE.py"
  goto :done
)

python -c "import frida" >nul 2>&1
if errorlevel 1 (
  echo Frida is not installed.
  echo Run 06_INSTALL_FRIDA.bat first.
  pause
  exit /b 1
)

python "%~dp004_RUNTIME_PROBE.py"

:done
set RC=%ERRORLEVEL%
if not "%RC%"=="0" echo [FAILED] Exit code %RC%
pause
exit /b %RC%
