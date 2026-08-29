@echo off
setlocal
cd /d "%~dp0"
start "PROJECT RELAY DISCORD" powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0RUN_DISCORD_BOT.ps1"
exit /b 0
