@echo off
setlocal
cd /d "%~dp0"
title FleetStream - Simulation Demo

echo ========================================================
echo   FleetStream Simulation Demo
echo ========================================================
echo [INFO] Running synthetic test distribution cycle...
echo.

if exist "%~dp0.venv\Scripts\python.exe" (
    set "PYTHON_CMD=%~dp0.venv\Scripts\python.exe"
) else (
    set "PYTHON_CMD=python"
)

"%PYTHON_CMD%" run_demo.py

echo.
echo ========================================================
echo   Demo completed. You can inspect mock_rig/devices/
echo ========================================================
echo.
pause
