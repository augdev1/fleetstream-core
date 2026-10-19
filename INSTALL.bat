@echo off
setlocal enabledelayedexpansion
title FleetStream - Dependency Installer

echo ========================================================
echo   FleetStream Dependency Installer
echo ========================================================
echo.

where python >nul 2>&1
if %errorlevel% neq 0 (
    where py >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] Python was not found on your system PATH.
        echo Please install Python 3.11 or newer and ensure "Add Python to PATH" is checked.
        echo Download: https://www.python.org/downloads/
        echo.
        pause
        exit /b 1
    ) else (
        set PYTHON_CMD=py
    )
) else (
    set PYTHON_CMD=python
)

echo [INFO] Python detected:
%PYTHON_CMD% --version
echo.

echo [INFO] Installing required dependencies from requirements.txt...
%PYTHON_CMD% -m pip install --upgrade pip
%PYTHON_CMD% -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to install dependencies. Please check permissions or network connectivity.
    echo.
    pause
    exit /b %errorlevel%
)

echo.
echo ========================================================
echo   [SUCCESS] All dependencies installed successfully.
echo   You can now launch the service using START_FLEETSTREAM.bat.
echo ========================================================
echo.
pause
