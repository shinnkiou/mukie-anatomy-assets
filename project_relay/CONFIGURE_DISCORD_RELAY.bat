@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0CONFIGURE_DISCORD_RELAY.ps1"
exit /b %errorlevel%
