@echo off
setlocal
chcp 65001 >nul

set "BRIDGE=%~dp0UKIE_AI_BRIDGE.exe"
set "RELEASE=%~dp0RELEASE_INFO.json"
set "WORK=%LOCALAPPDATA%\UKIE_AI_BRIDGE\acceptance"

if not exist "%BRIDGE%" (
  echo ERROR: UKIE_AI_BRIDGE.exe was not found next to this launcher.
  echo Keep all release files in the same folder.
  pause
  exit /b 2
)

if not exist "%RELEASE%" (
  echo ERROR: RELEASE_INFO.json was not found next to this launcher.
  echo Release binding is mandatory for physical acceptance.
  pause
  exit /b 2
)

echo UKIE AI BRIDGE - FIRST PHYSICAL ACCEPTANCE + SAFE HANDOFF
echo Workspace: %WORK%
echo Release info: %RELEASE%
echo.
echo On the first run, select a Google Drive for Desktop sync folder.
echo The Bridge creates a UKIE_AI_BRIDGE_INBOX folder inside it.
echo A local sync-folder copy is NOT treated as Google Drive readback verification.
echo.
"%BRIDGE%" acceptance-and-handoff --workspace "%WORK%" --release-info "%RELEASE%"
set "RC=%ERRORLEVEL%"
echo.
if "%RC%"=="0" (
  echo CORE ACCEPTANCE AND LOCAL HANDOFF FINISHED.
  echo The result is still NOT READY FOR AI until cloud discovery, raw Drive readback and release promotion checks pass.
) else (
  echo ACCEPTANCE OR HANDOFF REQUIRES REVIEW. Exit code: %RC%
)
echo Evidence workspace: %WORK%
echo.
pause
exit /b %RC%
