@echo off
setlocal enabledelayedexpansion
title FleetStream - Dependency Installer

echo ========================================================
echo   FleetStream Dependency Installer
echo ========================================================
echo.

set "SCRIPT_DIR=%~dp0"
set "VENV_DIR=%SCRIPT_DIR%.venv"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"

:: 1. Priority: check if local virtual environment already exists
if exist "%VENV_PY%" (
    echo [INFO] Detected virtual environment at:
    echo        %VENV_DIR%
    echo [INFO] Testing Python runtime...
    "%VENV_PY%" --version
    if !errorlevel! equ 0 (
        echo [INFO] Virtual environment is valid and ready.
        set "PYTHON_EXEC=%VENV_PY%"
        goto :INSTALL_DEPS
    )
)

:: 2. Locate working Python runtime on host system (avoiding WindowsApps alias)
set "HOST_PYTHON="

python -V >nul 2>&1
if !errorlevel! equ 0 (
    set "HOST_PYTHON=python"
    goto :CREATE_VENV
)

py -V >nul 2>&1
if !errorlevel! equ 0 (
    set "HOST_PYTHON=py"
    goto :CREATE_VENV
)

:: 3. Check for uv toolchain
set "UV_EXEC="
where uv >nul 2>&1
if !errorlevel! equ 0 (
    set "UV_EXEC=uv"
) else if exist "%USERPROFILE%\.local\bin\uv.exe" (
    set "UV_EXEC=%USERPROFILE%\.local\bin\uv.exe"
)

if defined UV_EXEC (
    echo [INFO] Using uv to configure isolated Python environment...
    "%UV_EXEC%" venv "%VENV_DIR%"
    if !errorlevel! neq 0 (
        echo [ERROR] uv failed to initialize virtual environment.
        pause
        exit /b 1
    )
    echo [INFO] Installing dependencies via uv...
    "%UV_EXEC%" pip install -r "%SCRIPT_DIR%requirements.txt" --python "%VENV_PY%"
    if !errorlevel! equ 0 goto :SUCCESS
)

:: 4. Attempt automated 1-click bootstrap (zero manual Python setup required)
echo [INFO] Python not found on system PATH.
echo [INFO] Attempting automated 1-click setup...
powershell -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex" >nul 2>&1
if exist "%USERPROFILE%\.local\bin\uv.exe" (
    set "UV_EXEC=%USERPROFILE%\.local\bin\uv.exe"
    echo [INFO] Automated bootstrapper configured.
    echo [INFO] Provisioning isolated Python environment and dependencies...
    "!UV_EXEC!" venv "%VENV_DIR%"
    "!UV_EXEC!" pip install -r "%SCRIPT_DIR%requirements.txt" --python "%VENV_PY%"
    if !errorlevel! equ 0 goto :SUCCESS
)

:: 5. Fallback: prompt user to install Python
echo [ERROR] Python 3.11+ was not found on your system.
echo.
echo Please install Python using the official installer:
echo 1. Download: https://www.python.org/downloads/
echo 2. IMPORTANT: Check "Add Python to PATH" during installation.
echo 3. Run INSTALL.bat again after installation.
echo.
pause
exit /b 1

:CREATE_VENV
echo [INFO] Using host Python:
!HOST_PYTHON! --version
echo [INFO] Creating local virtual environment at .venv...
!HOST_PYTHON! -m venv "%VENV_DIR%"
if !errorlevel! neq 0 (
    echo [ERROR] Failed to create virtual environment.
    pause
    exit /b !errorlevel!
)
set "PYTHON_EXEC=%VENV_PY%"

:INSTALL_DEPS
echo [INFO] Checking dependencies from requirements.txt...
"%PYTHON_EXEC%" -m pip install -r "%SCRIPT_DIR%requirements.txt"
if !errorlevel! neq 0 (
    echo.
    echo [ERROR] Dependency installation encountered an issue.
    pause
    exit /b !errorlevel!
)

:SUCCESS
echo.
echo ========================================================
echo   [SUCCESS] FleetStream environment ready!
echo   Run START_FLEETSTREAM.bat to launch the watcher daemon.
echo   Or run RUN_DEMO.bat to test with simulated videos.
echo ========================================================
echo.
pause
