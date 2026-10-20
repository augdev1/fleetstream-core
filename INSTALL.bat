@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
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

:: 3. Check for bundled tools\uv.exe or system uv toolchain
set "UV_EXEC="
if exist "%SCRIPT_DIR%tools\uv.exe" (
    set "UV_EXEC=%SCRIPT_DIR%tools\uv.exe"
) else (
    where uv >nul 2>&1
    if !errorlevel! equ 0 (
        set "UV_EXEC=uv"
    ) else if exist "%USERPROFILE%\.local\bin\uv.exe" (
        set "UV_EXEC=%USERPROFILE%\.local\bin\uv.exe"
    )
)

if defined UV_EXEC (
    echo [INFO] Using uv package manager to configure isolated Python environment...
    echo [INFO] Provisioning standalone Python 3.12 runtime and virtual environment...
    "%UV_EXEC%" venv "%VENV_DIR%" --python 3.12 --seed
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to initialize virtual environment with uv.
        pause
        exit /b 1
    )
    echo [INFO] Installing required dependencies...
    "%UV_EXEC%" pip install -r "%SCRIPT_DIR%requirements.txt" --python "%VENV_PY%"
    if !errorlevel! equ 0 goto :SUCCESS
)

:: 4. Attempt automated 1-click bootstrap (zero manual Python setup required)
echo [INFO] Python not found on system PATH.
echo [INFO] Automatically downloading Python 3.12 and dependencies...
powershell -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex" >nul 2>&1
if exist "%USERPROFILE%\.local\bin\uv.exe" (
    set "UV_EXEC=%USERPROFILE%\.local\bin\uv.exe"
    echo [INFO] Environment bootstrapper configured.
    echo [INFO] Downloading standalone Python 3.12 and setting up .venv...
    "!UV_EXEC!" venv "%VENV_DIR%" --python 3.12 --seed
    echo [INFO] Installing required dependencies...
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
