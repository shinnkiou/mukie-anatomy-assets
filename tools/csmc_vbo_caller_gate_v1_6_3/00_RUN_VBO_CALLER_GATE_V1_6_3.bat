@echo off
setlocal EnableExtensions
chcp 65001 >nul 2>&1
cd /d "%~dp0"
title CSMC VBO CALLER GATE V1.6.3

echo ============================================================
echo  CSMC VBO CALLER GATE V1.6.3
echo ============================================================
echo.
echo 日本語手順書: GUIDE_JA.txt
echo 実行前にMODELERを完全に閉じてください。
echo このBATはcaller/backtrace completion passだけを実行します。
echo cleanup / admin / save操作は行いません。
echo.
pause

py -3 -c "import frida" >nul 2>&1
if not errorlevel 1 (
  py -3 "%~dp001_VBO_CALLER_GATE_V1_6_3.py"
  goto :done
)

python -c "import frida" >nul 2>&1
if errorlevel 1 (
  echo [FAILED] Frida import failed.
  pause
  exit /b 1
)

python "%~dp001_VBO_CALLER_GATE_V1_6_3.py"

:done
set "RC=%ERRORLEVEL%"
echo.
if not "%RC%"=="0" echo [FAILED] Exit code %RC%
pause
exit /b %RC%
