@echo off
setlocal
title Install Frida for CSMC Probe

echo.
echo Installs Frida into your user Python environment.
echo.
pause

py -3 -m pip install --user frida frida-tools
if not errorlevel 1 goto :done

python -m pip install --user frida frida-tools

:done
echo.
echo Finished.
pause
