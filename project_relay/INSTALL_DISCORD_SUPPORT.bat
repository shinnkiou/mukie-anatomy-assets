@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
  py -3 -m pip install --user -r "%~dp0requirements-discord.txt"
  exit /b %errorlevel%
)

where python >nul 2>nul
if %errorlevel%==0 (
  python -m pip install --user -r "%~dp0requirements-discord.txt"
  exit /b %errorlevel%
)

echo ERROR: Python 3 was not found.
pause
exit /b 2
