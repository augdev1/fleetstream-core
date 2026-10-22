#!/usr/bin/env bash
# ========================================================
# FleetStream - Active Daemon Launcher (macOS)
# ========================================================
cd "$(dirname "$0")"

# Include standard macOS PATHs (Homebrew, local bins, cargo)
export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

clear 2>/dev/null || true

echo "========================================================"
echo "  FleetStream Orchestrator - Active Daemon (macOS)"
echo "========================================================"
echo "[INFO] Initializing continuous folder monitoring..."
echo "[INFO] Press Ctrl+C to stop the daemon at any time."
echo ""

PYTHON_CMD=""
if [ -x ".venv/bin/python3" ]; then
    PYTHON_CMD=".venv/bin/python3"
elif [ -x ".venv/bin/python" ]; then
    PYTHON_CMD=".venv/bin/python"
elif [ -f ".venv/bin/python3" ]; then
    PYTHON_CMD=".venv/bin/python3"
elif [ -f ".venv/bin/python" ]; then
    PYTHON_CMD=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD="python"
fi

if [ -z "$PYTHON_CMD" ]; then
    echo "[ERROR] Python environment not detected."
    echo "Please double-click INSTALL.command (or run ./install.sh) first."
    echo ""
    read -n 1 -s -r -p "Press any key to close..." 2>/dev/null || true
    echo ""
    exit 1
fi

"$PYTHON_CMD" watcher.py

echo ""
echo "[INFO] FleetStream session ended."
read -n 1 -s -r -p "Press any key to close..." 2>/dev/null || true
echo ""
