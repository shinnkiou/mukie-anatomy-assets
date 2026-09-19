@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo ============================================================
echo CSMC P1 - VTABLE DISPATCH MAP
echo ============================================================
echo.
echo Scope:
echo   - one-time check: 0x1400452b0
echo   - PW3DModelDataLoader: 9 slots
echo   - PWCanvas3DModelLoader: 9 slots
echo   - existing decompile is reused, not re-decompiled
echo   - call chain is bounded to depth 3
echo.
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp001_RUN_P1_VTABLE_DISPATCH.ps1"
set RC=%ERRORLEVEL%
echo.
echo ============================================================
echo P1 exit code: %RC%
echo This window will stay open.
echo ============================================================
pause
exit /b %RC%
