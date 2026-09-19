@echo off
setlocal EnableExtensions
chcp 65001 >nul 2>&1
cd /d "%~dp0"
title CSMC P0 GHIDRA TARGETED PASS

echo ============================================================
echo  CSMC P0 GHIDRA TARGETED PASS
echo ============================================================
echo.
echo ghidra_targets.txt に新規候補がある場合だけ実行します。
echo 日本語ガイド: GHIDRA_TARGETED_GUIDE_JA.txt
echo.
pause

powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp011_RUN_GHIDRA_TARGETS.ps1"
set "RC=%ERRORLEVEL%"

echo.
if not "%RC%"=="0" (
  echo [FAILED] Exit code %RC%
) else (
  echo [COMPLETE]
)
pause
exit /b %RC%
