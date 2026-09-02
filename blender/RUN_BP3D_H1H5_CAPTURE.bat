@echo off
setlocal EnableExtensions
chcp 65001 >nul
set "HERE=%~dp0"
set "ZIP=%HERE%BP3D_GRADUATION_DEADLINE_BUILD_V02_20260903.zip"
set "ROOT=%HERE%BP3D_GRADUATION_DEADLINE_BUILD_V02_20260903"
if not exist "%ROOT%\blender\BP3D_BUILD_DEADLINE_SCENE_V02.py" (
  if not exist "%ZIP%" (
    echo [ERROR] Put BP3D_GRADUATION_DEADLINE_BUILD_V02_20260903.zip next to this BAT.
    exit /b 10
  )
  powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -LiteralPath '%ZIP%' -DestinationPath '%HERE%' -Force"
)
set "BLENDER=%BLENDER_EXE%"
if not defined BLENDER for /f "delims=" %%I in ('where blender.exe 2^>nul') do if not defined BLENDER set "BLENDER=%%I"
if not defined BLENDER if exist "%ProgramFiles%\Blender Foundation\Blender 4.2\blender.exe" set "BLENDER=%ProgramFiles%\Blender Foundation\Blender 4.2\blender.exe"
if not defined BLENDER (
  echo [ERROR] Blender not found. Set BLENDER_EXE.
  exit /b 11
)
if not defined BP3D_CAPTURE_MODES set "BP3D_CAPTURE_MODES=FULL"
set "BP3D_CAPTURE_OUTPUT=%ROOT%\capture_h1h5"
"%BLENDER%" --background --python-expr "exec(compile(open(r'%ROOT%\blender\BP3D_BUILD_DEADLINE_SCENE_V02.py',encoding='utf-8').read(),r'%ROOT%\blender\BP3D_BUILD_DEADLINE_SCENE_V02.py','exec'));exec(compile(open(r'%HERE%BP3D_CAPTURE_H1H5_V01.py',encoding='utf-8').read(),r'%HERE%BP3D_CAPTURE_H1H5_V01.py','exec'))"
exit /b %ERRORLEVEL%
