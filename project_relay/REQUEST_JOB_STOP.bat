@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage: REQUEST_JOB_STOP.bat COMMAND_ID [SOFT^|HARD^|EMERGENCY]
  exit /b 2
)
set "CMDID=%~1"
set "MODE=%~2"
if "%MODE%"=="" set "MODE=SOFT"
if not exist "runtime\jobs\%CMDID%" (
  echo ERROR: job not found: %CMDID%
  exit /b 3
)
>"runtime\jobs\%CMDID%\STOP_REQUESTED.json" echo {"mode":"%MODE%","reason":"manual"}
echo Stop requested: %CMDID% [%MODE%]
exit /b 0
