@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 "%~dp0agent.py" --selftest
  exit /b %errorlevel%
)
where python >nul 2>nul
if %errorlevel%==0 (
  python "%~dp0agent.py" --selftest
  exit /b %errorlevel%
)
echo ERROR: Python 3 was not found.
pause
exit /b 2
