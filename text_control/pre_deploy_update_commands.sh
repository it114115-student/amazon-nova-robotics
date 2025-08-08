#!/bin/bash
# Pre-deployment script to update simple commands from MCP server
set -e

echo "=== Pre-deployment: Updating Simple Commands ==="

# Change to the text_control directory
cd "$(dirname "$0")"

echo "Extracting commands from MCP server tools..."

# Run the Python script to update commands
python3 update_simple_commands.py

echo "Verifying updated commands..."

# Test that the import works
python3 -c "from command_config.simple_commands import SIMPLE_COMMANDS; print(f'✓ Successfully loaded {len(SIMPLE_COMMANDS)} commands')"

# Test that the API can import everything
python3 -m py_compile routes/api.py && echo "✓ API syntax check passed"

echo "=== Simple commands update completed successfully! ==="
