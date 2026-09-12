@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo BP3D Modeler Observer P4 - read-only private runtime capture
echo.
echo 1. Open CLIP STUDIO MODELER and load the authorized model.
echo 2. This launcher starts the fail-closed observer.
echo 3. Press B in the observer to search/capture; press Q to package.
echo 4. Keep the resulting runtime ZIP private. Do not upload it to public GitHub.
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0BP3D_ModelerObserver_P4.ps1"
set "RC=%ERRORLEVEL%"
echo.
echo Observer exited with code %RC%.
pause
exit /b %RC%
