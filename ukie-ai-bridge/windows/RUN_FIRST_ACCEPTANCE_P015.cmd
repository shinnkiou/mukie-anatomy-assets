@echo off
setlocal
chcp 65001 >nul

set "BRIDGE=%~dp0UKIE_AI_BRIDGE.exe"
set "RELEASE=%~dp0RELEASE_INFO.json"
set "WORK=%LOCALAPPDATA%\UKIE_AI_BRIDGE\acceptance"

if not exist "%BRIDGE%" (
  echo ERROR: UKIE_AI_BRIDGE.exe was not found next to this launcher.
  pause
  exit /b 2
)
if not exist "%RELEASE%" (
  echo ERROR: RELEASE_INFO.json was not found next to this launcher.
  pause
  exit /b 2
)

echo UKIE AI BRIDGE P0.15 - PINNED BLENDER AUTO BOOTSTRAP
echo.
echo Step 1: Check exact Blender 4.2.23.
"%BRIDGE%" blender-discovery
if "%ERRORLEVEL%"=="0" goto blender_ready

echo.
echo Blender 4.2.23 was not found.
echo Downloading only the official portable ZIP and SHA256 from download.blender.org.
echo Existing Blender installations will not be removed or modified.
"%BRIDGE%" bootstrap-blender
if not "%ERRORLEVEL%"=="0" (
  echo ERROR: Verified Blender bootstrap failed.
  pause
  exit /b 2
)

:blender_ready
echo.
echo Step 2: Refresh handoff destination automatically.
"%BRIDGE%" configure-handoff
if not "%ERRORLEVEL%"=="0" (
  echo ERROR: Handoff configuration failed.
  pause
  exit /b 2
)

echo.
echo Step 3: Run physical acceptance.
"%BRIDGE%" acceptance-and-handoff --workspace "%WORK%" --release-info "%RELEASE%"
set "RC=%ERRORLEVEL%"
echo.
if "%RC%"=="0" (
  echo CORE ACCEPTANCE FINISHED.
  echo READY FOR AI still requires cloud Drive readback and later promotion checks.
) else (
  echo ACCEPTANCE OR HANDOFF REQUIRES REVIEW. Exit code: %RC%
)
echo Evidence workspace: %WORK%
echo.
pause
exit /b %RC%
