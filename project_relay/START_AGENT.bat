@echo off
setlocal
cd /d "%~dp0"
if not exist "runtime" mkdir "runtime"
if not exist "config\runners.json" copy /Y "config\runners.example.json" "config\runners.json" >nul
where py >nul 2>nul
if %errorlevel%==0 (
  start "PROJECT RELAY AGENT" /min py -3 "%~dp0agent.py"
  exit /b 0
)
where python >nul 2>nul
if %errorlevel%==0 (
  start "PROJECT RELAY AGENT" /min python "%~dp0agent.py"
  exit /b 0
)
echo ERROR: Python 3 was not found.
pause
exit /b 2
