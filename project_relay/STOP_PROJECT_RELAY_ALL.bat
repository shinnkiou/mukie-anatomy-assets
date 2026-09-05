@echo off
setlocal
cd /d "%~dp0"
if not exist "runtime" mkdir "runtime"
type nul > "runtime\STOP_AGENT"
type nul > "runtime\STOP_DISCORD"
echo STOP requested for PROJECT RELAY agent and Discord transport.
exit /b 0
