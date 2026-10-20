#!/usr/bin/env bash
cd "$(dirname "$0")"
clear

echo "========================================================"
echo "  FleetStream Dependency Installer (macOS)"
echo "========================================================"
echo ""

VENV_DIR=".venv"
VENV_PY="$VENV_DIR/bin/python3"

# 1. Check if virtual environment already exists
if [ -f "$VENV_PY" ]; then
    echo "[INFO] Detected virtual environment at: $VENV_DIR"
    echo "[INFO] Testing runtime..."
    "$VENV_PY" --version
    echo "[INFO] Installing/verifying dependencies..."
    "$VENV_PY" -m pip install -r requirements.txt
    echo ""
    echo "========================================================"
    echo "  [SUCCESS] FleetStream is ready on macOS!"
    echo "  Double-click START_FLEETSTREAM.command to launch."
    echo "========================================================"
    read -n 1 -s -r -p "Press any key to close..."
    echo ""
    exit 0
fi

# 2. Check for host Python 3
if command -v python3 >/dev/null 2>&1; then
    HOST_PY="python3"
elif command -v python >/dev/null 2>&1; then
    HOST_PY="python"
else
    HOST_PY=""
fi

if [ -n "$HOST_PY" ]; then
    echo "[INFO] Using host Python: $($HOST_PY --version)"
    echo "[INFO] Creating virtual environment at .venv..."
    "$HOST_PY" -m venv "$VENV_DIR"
    "$VENV_PY" -m pip install --upgrade pip
    "$VENV_PY" -m pip install -r requirements.txt
    echo ""
    echo "========================================================"
    echo "  [SUCCESS] FleetStream is ready on macOS!"
    echo "  Double-click START_FLEETSTREAM.command to launch."
    echo "========================================================"
    read -n 1 -s -r -p "Press any key to close..."
    echo ""
    exit 0
fi

# 3. Automated bootstrap via uv if Python is missing
echo "[INFO] Python not found on system PATH."
echo "[INFO] Downloading standalone Python 3.12..."
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

if command -v uv >/dev/null 2>&1; then
    uv venv "$VENV_DIR" --python 3.12 --seed
    uv pip install -r requirements.txt --python "$VENV_PY"
    echo ""
    echo "========================================================"
    echo "  [SUCCESS] FleetStream is ready on macOS!"
    echo "  Double-click START_FLEETSTREAM.command to launch."
    echo "========================================================"
    read -n 1 -s -r -p "Press any key to close..."
    echo ""
    exit 0
fi

echo "[ERROR] Could not automatically configure Python. Please install Python 3.11+ from https://www.python.org"
read -n 1 -s -r -p "Press any key to close..."
echo ""
exit 1
