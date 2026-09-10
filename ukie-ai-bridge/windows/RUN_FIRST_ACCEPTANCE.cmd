@echo off
setlocal
chcp 65001 >nul

set "BRIDGE=%~dp0UKIE_AI_BRIDGE.exe"
set "WORK=%LOCALAPPDATA%\UKIE_AI_BRIDGE\acceptance"

if not exist "%BRIDGE%" (
  echo ERROR: UKIE_AI_BRIDGE.exe was not found next to this launcher.
  echo Put RUN_FIRST_ACCEPTANCE.cmd and UKIE_AI_BRIDGE.exe in the same folder.
  pause
  exit /b 2
)

echo UKIE AI BRIDGE - FIRST PHYSICAL ACCEPTANCE
echo Workspace: %WORK%
echo.
"%BRIDGE%" physical-acceptance --workspace "%WORK%"
set "RC=%ERRORLEVEL%"
echo.
if "%RC%"=="0" (
  echo CORE ACCEPTANCE FINISHED.
  echo The result is still NOT READY FOR AI until Drive readback and release promotion checks pass.
) else (
  echo ACCEPTANCE REQUIRES REVIEW. Exit code: %RC%
)
echo Evidence workspace: %WORK%
echo.
pause
exit /b %RC%
