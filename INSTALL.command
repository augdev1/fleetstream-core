#!/usr/bin/env bash
# ========================================================
# FleetStream - macOS Installer
# ========================================================
set -e

# Change directory to the folder containing this script
cd "$(dirname "$0")"

# Include standard macOS PATHs (Homebrew Apple Silicon & Intel, local bins, cargo)
export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

clear 2>/dev/null || true

echo "========================================================"
echo "  FleetStream Dependency Installer (macOS)"
echo "========================================================"
echo ""

VENV_DIR=".venv"

# Trap errors so terminal window does not abruptly close before user reads error
trap 'echo ""; echo "[ERROR] Installation encountered an issue. See above for details."; read -n 1 -s -r -p "Press any key to close..." 2>/dev/null || true; echo ""' ERR

# Function to test if a python command is functional (not a broken Xcode CLT shim)
is_functional_python() {
    local cmd="$1"
    if ! command -v "$cmd" >/dev/null 2>&1; then
        return 1
    fi
    "$cmd" -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >/dev/null 2>&1
}

# 1. Check if virtual environment already exists and works
if [ -x "$VENV_DIR/bin/python3" ] || [ -x "$VENV_DIR/bin/python" ]; then
    VENV_PY="$VENV_DIR/bin/python3"
    [ -x "$VENV_PY" ] || VENV_PY="$VENV_DIR/bin/python"
    
    echo "[INFO] Existing virtual environment found at: $VENV_DIR"
    echo "[INFO] Updating/verifying dependencies..."
    "$VENV_PY" -m pip install -r requirements.txt
    echo ""
    echo "========================================================"
    echo "  [SUCCESS] FleetStream is installed and ready on macOS!"
    echo "  Double-click START_FLEETSTREAM.command to launch."
    echo "========================================================"
    read -n 1 -s -r -p "Press any key to close..." 2>/dev/null || true
    echo ""
    exit 0
fi

# 2. Check if uv is available or can be used
if command -v uv >/dev/null 2>&1; then
    echo "[INFO] Found uv package manager. Creating virtual environment..."
    uv venv "$VENV_DIR" --python 3.12 --seed
    VENV_PY="$VENV_DIR/bin/python"
    [ -x "$VENV_PY" ] || VENV_PY="$VENV_DIR/bin/python3"
    uv pip install -r requirements.txt --python "$VENV_PY"
    echo ""
    echo "========================================================"
    echo "  [SUCCESS] FleetStream is installed and ready on macOS!"
    echo "  Double-click START_FLEETSTREAM.command to launch."
    echo "========================================================"
    read -n 1 -s -r -p "Press any key to close..." 2>/dev/null || true
    echo ""
    exit 0
fi

# 3. Check for functional system/homebrew Python 3
FOUND_PY=""
for candidate in python3.13 python3.12 python3.11 python3.10 python3; do
    if is_functional_python "$candidate"; then
        FOUND_PY="$candidate"
        break
    fi
done

if [ -n "$FOUND_PY" ]; then
    echo "[INFO] Using Python: $($FOUND_PY --version)"
    echo "[INFO] Creating virtual environment at: $VENV_DIR..."
    "$FOUND_PY" -m venv "$VENV_DIR"
    VENV_PY="$VENV_DIR/bin/python3"
    [ -x "$VENV_PY" ] || VENV_PY="$VENV_DIR/bin/python"
    
    "$VENV_PY" -m ensurepip >/dev/null 2>&1 || true
    "$VENV_PY" -m pip install --upgrade pip >/dev/null 2>&1 || true
    "$VENV_PY" -m pip install -r requirements.txt
    echo ""
    echo "========================================================"
    echo "  [SUCCESS] FleetStream is installed and ready on macOS!"
    echo "  Double-click START_FLEETSTREAM.command to launch."
    echo "========================================================"
    read -n 1 -s -r -p "Press any key to close..." 2>/dev/null || true
    echo ""
    exit 0
fi

# 4. If no functional Python, bootstrap uv standalone (which downloads standalone Python 3.12)
echo "[INFO] No functional Python 3.10+ found on system PATH."
echo "[INFO] Bootstrapping standalone Python via uv installer..."
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

if command -v uv >/dev/null 2>&1; then
    uv venv "$VENV_DIR" --python 3.12 --seed
    VENV_PY="$VENV_DIR/bin/python"
    [ -x "$VENV_PY" ] || VENV_PY="$VENV_DIR/bin/python3"
    uv pip install -r requirements.txt --python "$VENV_PY"
    echo ""
    echo "========================================================"
    echo "  [SUCCESS] FleetStream is installed and ready on macOS!"
    echo "  Double-click START_FLEETSTREAM.command to launch."
    echo "========================================================"
    read -n 1 -s -r -p "Press any key to close..." 2>/dev/null || true
    echo ""
    exit 0
fi

echo "[ERROR] Failed to configure Python automatically."
echo "Please install Python 3.11+ from https://www.python.org or via Homebrew: 'brew install python'"
read -n 1 -s -r -p "Press any key to close..." 2>/dev/null || true
echo ""
exit 1
