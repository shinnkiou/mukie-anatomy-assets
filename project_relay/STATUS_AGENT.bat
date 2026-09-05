@echo off
setlocal
cd /d "%~dp0"
echo === PROJECT RELAY AGENT STATUS ===
if exist "runtime\agent_state.json" (
  type "runtime\agent_state.json"
) else (
  echo Agent state not found.
)
echo.
if exist "runtime\agent_heartbeat.json" (
  echo === HEARTBEAT ===
  type "runtime\agent_heartbeat.json"
)
echo.
pause
exit /b 0
