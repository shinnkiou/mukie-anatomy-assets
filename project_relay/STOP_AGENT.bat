@echo off
setlocal
cd /d "%~dp0"
if not exist "runtime" mkdir "runtime"
type nul > "runtime\STOP_AGENT"
echo STOP requested.
exit /b 0
