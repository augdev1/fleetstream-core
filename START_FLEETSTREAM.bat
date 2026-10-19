@echo off
setlocal
title FleetStream Orchestrator - Active Daemon

echo ========================================================
echo   FleetStream Orchestrator - Active Daemon
echo ========================================================
echo [INFO] Initializing continuous folder monitoring...
echo [INFO] Press Ctrl+C to stop the daemon at any time.
echo.

if exist "%~dp0.venv\Scripts\python.exe" (
    set "PYTHON_CMD=%~dp0.venv\Scripts\python.exe"
) else (
    where python >nul 2>&1
    if %errorlevel% neq 0 (
        where py >nul 2>&1
        if %errorlevel% neq 0 (
            echo [ERROR] Python is not installed or not available on PATH.
            echo Please run INSTALL.bat first or install Python 3.11+.
            echo.
            pause
            exit /b 1
        ) else (
            set PYTHON_CMD=py
        )
    ) else (
        set PYTHON_CMD=python
    )
)

%PYTHON_CMD% watcher.py

if %errorlevel% neq 0 (
    echo.
    echo [WARNING] FleetStream watcher exited with status code: %errorlevel%
)

echo.
echo [INFO] FleetStream session ended.
pause
