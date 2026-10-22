#!/usr/bin/env bash
# ========================================================
# FleetStream - Terminal Shell Launcher (macOS / Linux)
# ========================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$SCRIPT_DIR/START_FLEETSTREAM.command" "$@"
