@echo off
setlocal EnableExtensions
chcp 65001 >nul 2>&1
cd /d "%~dp0"
title CSMC VBO WRITER PROBE V1.6.2 VALIDATED PLATEAU

echo ============================================================
echo  CSMC VBO WRITER PROBE V1.6.2 VALIDATED PLATEAU
echo ============================================================
echo.
echo Close MODELER before starting.
echo This BAT only runs the Frida probe.
echo No cleanup / admin / save operation is included.
echo.
pause

py -3 -c "import frida" >nul 2>&1
if not errorlevel 1 (
  py -3 "%~dp001_VBO_WRITER_PROBE_V1_6_2.py"
  goto :done
)

python -c "import frida" >nul 2>&1
if errorlevel 1 (
  echo [FAILED] Frida import failed.
  pause
  exit /b 1
)

python "%~dp001_VBO_WRITER_PROBE_V1_6_2.py"

:done
set "RC=%ERRORLEVEL%"
echo.
if not "%RC%"=="0" echo [FAILED] Exit code %RC%
pause
exit /b %RC%
