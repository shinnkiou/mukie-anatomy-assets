@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul
set "HERE=%~dp0"
set "ZIP=%HERE%BP3D_GRADUATION_DEADLINE_BUILD_V02_20260903.zip"
set "ROOT=%HERE%BP3D_GRADUATION_DEADLINE_BUILD_V02_20260903"
if not exist "%ROOT%\blender\BP3D_BUILD_DEADLINE_SCENE_V02.py" (
  if not exist "%ZIP%" (
    echo [ERROR] Put BP3D_GRADUATION_DEADLINE_BUILD_V02_20260903.zip next to this BAT, or extract it to %ROOT%
    exit /b 10
  )
  echo [INFO] Extracting Deadline Build V02...
  powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -LiteralPath '%ZIP%' -DestinationPath '%HERE%' -Force"
)
set "BP3D_DEADLINE_ROOT=%ROOT%"
set "BLENDER=%BLENDER_EXE%"
if not defined BLENDER (
  for /f "delims=" %%I in ('where blender.exe 2^>nul') do if not defined BLENDER set "BLENDER=%%I"
)
if not defined BLENDER if exist "%ProgramFiles%\Blender Foundation\Blender 4.2\blender.exe" set "BLENDER=%ProgramFiles%\Blender Foundation\Blender 4.2\blender.exe"
if not defined BLENDER if exist "%ProgramFiles%\Blender Foundation\Blender 4.3\blender.exe" set "BLENDER=%ProgramFiles%\Blender Foundation\Blender 4.3\blender.exe"
if not defined BLENDER if exist "%ProgramFiles%\Blender Foundation\Blender 4.4\blender.exe" set "BLENDER=%ProgramFiles%\Blender Foundation\Blender 4.4\blender.exe"
if not defined BLENDER (
  echo [ERROR] Blender was not found. Set environment variable BLENDER_EXE to blender.exe and run again.
  exit /b 11
)
echo [INFO] Blender: %BLENDER%
echo [INFO] Package: %BP3D_DEADLINE_ROOT%
"%BLENDER%" --background --python "%HERE%BP3D_DEADLINE_BUILD_HEADLESS_QA_V02.py"
set RC=%ERRORLEVEL%
if not "%RC%"=="0" (
  echo [FAIL] BP3D QA returned code %RC%
  exit /b %RC%
)
echo [PASS] Results: %ROOT%\qa_output\BP3D_DEADLINE_BUILD_QA_RESULT.json
exit /b 0
