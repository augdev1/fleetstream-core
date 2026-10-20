#!/usr/bin/env bash
cd "$(dirname "$0")"
clear

echo "========================================================"
echo "  FleetStream Orchestrator - Active Daemon (macOS)"
echo "========================================================"
echo "[INFO] Initializing continuous folder monitoring..."
echo "[INFO] Press Ctrl+C to stop the daemon at any time."
echo ""

if [ -f ".venv/bin/python3" ]; then
    PYTHON_CMD=".venv/bin/python3"
elif [ -f ".venv/bin/python" ]; then
    PYTHON_CMD=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD="python"
else
    echo "[ERROR] Python environment not detected."
    echo "Please double-click INSTALL.command first."
    echo ""
    read -n 1 -s -r -p "Press any key to close..."
    echo ""
    exit 1
fi

"$PYTHON_CMD" watcher.py

echo ""
echo "[INFO] FleetStream session ended."
read -n 1 -s -r -p "Press any key to close..."
echo ""
