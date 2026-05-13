#!/bin/bash
set -e

# Ensure we are in the script directory
cd "$(dirname "$0")"

# Define local venv path
VENV_DIR="./.venv"
VENV_PYTHON="$VENV_DIR/bin/python"
VENV_PIP="$VENV_DIR/bin/pip"

# Create venv if it doesn't exist, using absolute local path
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi

# Ensure dependencies are installed only in the local venv
if [ ! -f "$VENV_DIR/.installed" ]; then
    "$VENV_PIP" install -q -r requirements.txt
    touch "$VENV_DIR/.installed"
fi

# Execute skill using the local venv python exclusively
exec "$VENV_PYTHON" scripts/skill.py "$@"
