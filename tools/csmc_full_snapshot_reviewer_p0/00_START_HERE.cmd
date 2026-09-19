@echo off
setlocal EnableExtensions
cd /d "%~dp0"

rem ASCII-only emergency launcher.
rem It opens a NEW cmd.exe with /K so the diagnostic window stays open
rem even if this outer launcher exits immediately.

start "CSMC P0 DIAGNOSTIC" %ComSpec% /D /K call "%~dp001_P0_INNER_DIAGNOSTIC.cmd"
exit /b 0
