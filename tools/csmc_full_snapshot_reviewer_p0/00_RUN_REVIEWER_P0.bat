@echo off
setlocal EnableExtensions
chcp 65001 >nul 2>&1
cd /d "%~dp0"
title CSMC FULL SNAPSHOT REVIEWER P0

echo ============================================================
echo  CSMC FULL SNAPSHOT REVIEWER P0
echo ============================================================
echo.
echo 日本語ガイド: GUIDE_JA.txt
echo.
echo 対象:
echo   CSMC_FULL_SNAPSHOT_20260914_214659.zip
echo   CSMC_FULL_SNAPSHOT_FOCUSED_20260914_232435.zip
echo.
echo 元ZIPは変更しません。
echo 広域再調査ではなく、consumer候補のtargeted reviewです。
echo.
pause

powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp001_RUN_REVIEWER_P0.ps1"
set "RC=%ERRORLEVEL%"

echo.
if not "%RC%"=="0" (
  echo [FAILED] Exit code %RC%
) else (
  echo [COMPLETE]
)
pause
exit /b %RC%
