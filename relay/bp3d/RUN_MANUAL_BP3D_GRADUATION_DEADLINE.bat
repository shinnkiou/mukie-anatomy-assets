@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul
set "WS=%~dp0..\..\"
if exist "%~dp0..\..\00_INPUT" set "WS=%~dp0..\..\"
set "INPUT=%WS%00_INPUT\BP3D_GRADUATION_ONE_CLICK_V01_20260903.zip"
set "WORK=%WS%20_WORK\BP3D_GRADUATION_DEADLINE_20260903_01"
set "OUT=%WS%30_OUTPUT"
set "REPORT=%WS%40_REPORT"
set "LOG=%WS%90_LOG\BP3D_GRADUATION_DEADLINE_20260903_01.log"
set "ARCH=%WS%99_ARCHIVE"
set "EXPECTED_SHA=8a2cfc9a9f89dcb4161bf86a23222bf4db464bb590601f2984c055650d02098e"

echo [%date% %time%] START > "%LOG%"
if not exist "%INPUT%" (
  echo [ERROR] input ZIP missing: %INPUT%
  echo input ZIP missing>>"%LOG%"
  >"%REPORT%\FAILURE_BP3D_GRADUATION_DEADLINE_20260903_01.txt" echo input ZIP missing
  exit /b 10
)
for /f "tokens=*" %%H in ('powershell -NoProfile -Command "(Get-FileHash -Algorithm SHA256 -LiteralPath ''%INPUT%'').Hash.ToLower()"') do set "ACTUAL_SHA=%%H"
if /I not "%ACTUAL_SHA%"=="%EXPECTED_SHA%" (
  echo [ERROR] SHA mismatch. Expected %EXPECTED_SHA% got %ACTUAL_SHA%
  echo SHA mismatch>>"%LOG%"
  >"%REPORT%\FAILURE_BP3D_GRADUATION_DEADLINE_20260903_01.txt" echo SHA mismatch
  exit /b 11
)
if exist "%WORK%" (
  for /f %%T in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "STAMP=%%T"
  move "%WORK%" "%ARCH%\BP3D_GRADUATION_DEADLINE_20260903_01_!STAMP!" >nul
)
mkdir "%WORK%" 2>nul
powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -LiteralPath '%INPUT%' -DestinationPath '%WORK%' -Force"
if errorlevel 1 goto :fail_expand
pushd "%WORK%"
call "RUN_BP3D_GRADUATION_PIPELINE.bat"
set "RC=%ERRORLEVEL%"
popd
if not "%RC%"=="0" goto :fail_pipeline
set "BUILD=%WORK%\BP3D_GRADUATION_DEADLINE_BUILD_V02_20260903"
set "PIPE=%BUILD%\BP3D_GRADUATION_PIPELINE_RESULT.json"
set "QA=%BUILD%\qa_output\BP3D_DEADLINE_BUILD_QA_RESULT.json"
set "CAP=%BUILD%\capture_h1h5\BP3D_H1H5_CAPTURE_RESULT.json"
set "CAPZIP=%BUILD%\BP3D_GRADUATION_CAPTURE_OUTPUT.zip"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$paths=@('%PIPE%','%QA%','%CAP%','%CAPZIP%'); foreach($p in $paths){if(!(Test-Path -LiteralPath $p)){exit 21}}; foreach($p in @('%PIPE%','%QA%','%CAP%')){$j=Get-Content -Raw -LiteralPath $p|ConvertFrom-Json; if($j.status -ne 'PASS'){exit 22}}"
if errorlevel 1 goto :fail_validate
copy /Y "%CAPZIP%" "%OUT%\BP3D_GRADUATION_CAPTURE_OUTPUT.zip" >nul
copy /Y "%PIPE%" "%REPORT%\BP3D_GRADUATION_PIPELINE_RESULT.json" >nul
copy /Y "%QA%" "%REPORT%\BP3D_DEADLINE_BUILD_QA_RESULT.json" >nul
copy /Y "%CAP%" "%REPORT%\BP3D_H1H5_CAPTURE_RESULT.json" >nul
powershell -NoProfile -Command "$h=(Get-FileHash -Algorithm SHA256 -LiteralPath '%OUT%\BP3D_GRADUATION_CAPTURE_OUTPUT.zip').Hash.ToLower(); ($h+'  BP3D_GRADUATION_CAPTURE_OUTPUT.zip') | Set-Content -Encoding ascii -LiteralPath '%OUT%\BP3D_GRADUATION_CAPTURE_OUTPUT.zip.sha256'"
>"%REPORT%\SUCCESS_BP3D_GRADUATION_DEADLINE_20260903_01.txt" echo PASS %date% %time%
echo [%date% %time%] PASS>>"%LOG%"
echo [PASS] Fresh validated outputs copied to 30_OUTPUT and 40_REPORT.
exit /b 0
:fail_expand
>"%REPORT%\FAILURE_BP3D_GRADUATION_DEADLINE_20260903_01.txt" echo Expand-Archive failed %date% %time%
echo [%date% %time%] FAIL expand>>"%LOG%"
exit /b 12
:fail_pipeline
>"%REPORT%\FAILURE_BP3D_GRADUATION_DEADLINE_20260903_01.txt" echo Pipeline failed rc=%RC% %date% %time%
echo [%date% %time%] FAIL pipeline rc=%RC%>>"%LOG%"
echo [STOP] Pipeline failed. No stale output promoted.
exit /b %RC%
:fail_validate
>"%REPORT%\FAILURE_BP3D_GRADUATION_DEADLINE_20260903_01.txt" echo Result validation failed %date% %time%
echo [%date% %time%] FAIL validation>>"%LOG%"
echo [STOP] Result validation failed. No stale output promoted.
exit /b 23
