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

echo UKIE AI BRIDGE P0.14 - AUTO HANDOFF ACCEPTANCE
echo Workspace: %WORK%
echo Release info: %RELEASE%
echo.
echo The Bridge will automatically look for a Google Drive for desktop location.
echo If no safe Drive candidate is found, evidence is kept in a local outbox and the run continues.
echo A local copy never counts as Google Drive readback verification.
echo.
"%BRIDGE%" acceptance-and-handoff --workspace "%WORK%" --release-info "%RELEASE%"
set "RC=%ERRORLEVEL%"
echo.
if "%RC%"=="0" (
  echo CORE ACCEPTANCE FINISHED.
  echo Check the JSON result for DRIVE_SYNC_CANDIDATE or LOCAL_OUTBOX_ONLY.
  echo READY FOR AI still requires cloud Drive readback and later promotion checks.
) else (
  echo ACCEPTANCE OR HANDOFF REQUIRES REVIEW. Exit code: %RC%
)
echo Evidence workspace: %WORK%
echo.
pause
exit /b %RC%
