@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0SETUP_DISCORD_TOKEN.ps1"
exit /b %errorlevel%
