@echo off
setlocal
cd /d "%~dp0"
echo === PROJECT RELAY AGENT ===
if exist "runtime\agent_state.json" (type "runtime\agent_state.json") else (echo Agent state not found.)
echo.
echo === AGENT HEARTBEAT ===
if exist "runtime\agent_heartbeat.json" (type "runtime\agent_heartbeat.json") else (echo Agent heartbeat not found.)
echo.
echo === DISCORD TRANSPORT ===
if exist "runtime\discord_state.json" (type "runtime\discord_state.json") else (echo Discord state not found.)
echo.
echo === DISCORD HEARTBEAT ===
if exist "runtime\discord_heartbeat.json" (type "runtime\discord_heartbeat.json") else (echo Discord heartbeat not found.)
echo.
pause
exit /b 0
