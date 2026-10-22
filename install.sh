#!/usr/bin/env bash
# ========================================================
# FleetStream - Terminal Shell Installer (macOS / Linux)
# ========================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$SCRIPT_DIR/INSTALL.command" "$@"
