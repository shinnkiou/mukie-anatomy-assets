@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul
set "HERE=%~dp0"
set "ROOT=%HERE%BP3D_GRADUATION_DEADLINE_BUILD_V02_20260903"
set "QAJSON=%ROOT%\qa_output\BP3D_DEADLINE_BUILD_QA_RESULT.json"
set "CAPJSON=%ROOT%\capture_h1h5\BP3D_H1H5_CAPTURE_RESULT.json"

echo ============================================================
echo BP3D Graduation One-Click Pipeline V0.1
echo 1. Assemble + real Blender QA
echo 2. Fail-closed PASS gate
echo 3. H1-H5 capture
echo 4. Package render outputs
echo ============================================================

call "%HERE%RUN_BP3D_DEADLINE_BUILD_QA.bat"
if errorlevel 1 (
  echo [STOP] Real Blender QA failed. Capture was NOT started.
  exit /b 20
)

powershell -NoProfile -ExecutionPolicy Bypass -Command "$p='%QAJSON%'; if(!(Test-Path -LiteralPath $p)){exit 21}; $j=Get-Content -Raw -LiteralPath $p | ConvertFrom-Json; if($j.status -ne 'PASS'){exit 22}"
if errorlevel 1 (
  echo [STOP] QA result JSON is missing or not PASS. Capture was NOT started.
  exit /b 22
)

if not defined BP3D_CAPTURE_MODES set "BP3D_CAPTURE_MODES=FULL,ARM_ISOLATED,LEG_ISOLATED,TORSO_ISOLATED"
echo [INFO] Capture modes: %BP3D_CAPTURE_MODES%
call "%HERE%RUN_BP3D_H1H5_CAPTURE.bat"
if errorlevel 1 (
  echo [STOP] H1-H5 capture failed. Existing QA/capture outputs are preserved.
  exit /b 30
)

powershell -NoProfile -ExecutionPolicy Bypass -Command "$p='%CAPJSON%'; if(!(Test-Path -LiteralPath $p)){exit 31}; $j=Get-Content -Raw -LiteralPath $p | ConvertFrom-Json; if($j.status -ne 'PASS'){exit 32}"
if errorlevel 1 (
  echo [STOP] Capture result JSON is missing or not PASS.
  exit /b 32
)

powershell -NoProfile -ExecutionPolicy Bypass -Command "$src='%ROOT%\capture_h1h5'; $dst='%ROOT%\BP3D_GRADUATION_CAPTURE_OUTPUT.zip'; if(Test-Path -LiteralPath $dst){Remove-Item -LiteralPath $dst -Force}; Compress-Archive -LiteralPath ($src+'\*') -DestinationPath $dst -CompressionLevel Optimal; $qa=Get-Content -Raw -LiteralPath '%QAJSON%' | ConvertFrom-Json; $cap=Get-Content -Raw -LiteralPath '%CAPJSON%' | ConvertFrom-Json; $o=[ordered]@{schema='bp3d.graduation.one_click.result.v01';status='PASS';finished_at=(Get-Date).ToString('o');qa_status=$qa.status;capture_status=$cap.status;capture_modes=$cap.modes;render_count=$cap.renders.Count;capture_zip=$dst;source_mutation=0;semantic_mutation=0}; $o|ConvertTo-Json -Depth 8|Set-Content -Encoding UTF8 -LiteralPath '%ROOT%\BP3D_GRADUATION_PIPELINE_RESULT.json'"
if errorlevel 1 (
  echo [WARN] Renders succeeded but packaging/result JSON failed.
  exit /b 40
)

echo [PASS] Graduation pipeline complete.
echo [PASS] QA: %QAJSON%
echo [PASS] Capture result: %CAPJSON%
echo [PASS] Output ZIP: %ROOT%\BP3D_GRADUATION_CAPTURE_OUTPUT.zip
exit /b 0
