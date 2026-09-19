@echo off
setlocal EnableExtensions
chcp 65001 >nul 2>&1
cd /d "%~dp0"
title CSMC FULL SNAPSHOT REVIEWER P0 SAFE LAUNCHER

set "ROOT=C:\Users\nurun\CSMC_ANALYSIS\PRIVATE_FULL_SNAPSHOT"
set "LOG=%ROOT%\REVIEWER_P0_LAUNCH.log"

if not exist "%ROOT%" mkdir "%ROOT%" >nul 2>&1

(
  echo ============================================================
  echo CSMC FULL SNAPSHOT REVIEWER P0 SAFE LAUNCHER
  echo ============================================================
  echo Started: %DATE% %TIME%
  echo ScriptDir: %CD%
  echo.
) > "%LOG%"

echo ============================================================
echo  CSMC FULL SNAPSHOT REVIEWER P0 SAFE LAUNCHER
echo ============================================================
echo.
echo この版は、エラーが出ても画面を閉じません。
echo ログ:
echo   %LOG%
echo.

if not exist "%~dp001_RUN_REVIEWER_P0.ps1" (
  echo [FAILED] 01_RUN_REVIEWER_P0.ps1 が同じフォルダにありません。
  echo ZIPの中から直接実行せず、フォルダを展開してから実行してください。
  >>"%LOG%" echo [FAILED] Missing 01_RUN_REVIEWER_P0.ps1
  goto :hold
)

if not exist "%~dp002_ANALYZE_TARGETED_SNAPSHOT.py" (
  echo [FAILED] 02_ANALYZE_TARGETED_SNAPSHOT.py が同じフォルダにありません。
  >>"%LOG%" echo [FAILED] Missing 02_ANALYZE_TARGETED_SNAPSHOT.py
  goto :hold
)

if not exist "%~dp0KNOWN_FACTS.json" (
  echo [FAILED] KNOWN_FACTS.json が同じフォルダにありません。
  >>"%LOG%" echo [FAILED] Missing KNOWN_FACTS.json
  goto :hold
)

echo [PASS] 必要ファイルを確認しました。
echo.
echo Enterを押すとReviewer P0を開始します。
pause >nul

echo.
echo PowerShellを起動します...
echo 終了・失敗後もPowerShell画面を残します。
echo.

powershell.exe -NoLogo -NoProfile -NoExit -ExecutionPolicy Bypass -Command ^
  "& { try { & '%~dp001_RUN_REVIEWER_P0.ps1' *>&1 | Tee-Object -FilePath '%LOG%' -Append } catch { Write-Host ''; Write-Host '[POWERSHELL ERROR]' -ForegroundColor Red; Write-Host $_.Exception.Message -ForegroundColor Red; $_ | Out-String | Add-Content -LiteralPath '%LOG%'; }; Write-Host ''; Write-Host '--- 画面は自動では閉じません ---' -ForegroundColor Yellow; Write-Host '終了する場合だけ exit と入力してください。' -ForegroundColor Yellow }"

set "RC=%ERRORLEVEL%"
>>"%LOG%" echo Launcher PowerShell exit code: %RC%

:hold
echo.
echo ============================================================
echo ここで停止しています。画面は自動では閉じません。
echo ============================================================
echo.
echo ログ:
echo   %LOG%
echo.
echo この画面の内容か REVIEWER_P0_LAUNCH.log を送ってください。
echo.
cmd /k
