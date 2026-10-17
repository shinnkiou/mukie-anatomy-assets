@echo off
setlocal
cd /d "%~dp0"
call "%~dp0START_AGENT.bat"
if not %errorlevel%==0 exit /b %errorlevel%
call "%~dp0START_DISCORD_BOT.bat"
exit /b %errorlevel%
