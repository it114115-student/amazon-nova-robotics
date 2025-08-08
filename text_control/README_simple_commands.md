# Simple Commands Management

This directory contains the configuration and scripts for managing robot commands that bypass LLM classification for better performance.

## Files

- `config/simple_commands.py` - Configuration file containing the SIMPLE_COMMANDS set
- `update_simple_commands.py` - Script to auto-update commands from MCP server analysis
- `pre_deploy_update_commands.sh` - Pre-deployment script for CI/CD
- `demo_extract_commands.py` - Demo script showing command extraction

## Usage

### Manual Update

```bash
python3 update_simple_commands.py
```

### Pre-deployment (CI/CD)

```bash
./pre_deploy_update_commands.sh
```

### Testing Command Import

```python
from config.simple_commands import SIMPLE_COMMANDS
print(f"Loaded {len(SIMPLE_COMMANDS)} commands")
```

## How It Works

1. **Command Extraction**: The update script scans MCP server tools and robot client code
2. **Pattern Matching**: Looks for `execute_action("command")` calls and action parameters
3. **Categorization**: Groups commands by type (movement, dance, combat, etc.)
4. **Generation**: Creates new `simple_commands.py` with organized command sets

## Benefits

- **Performance**: Simple commands bypass expensive LLM classification (2-4 second speedup)
- **Accuracy**: Commands are extracted directly from implementation code
- **Maintainability**: Auto-sync with MCP server changes during deployment
- **Flexibility**: Supports command variations via normalization (camelCase, spaces, etc.)

## Integration

The API automatically imports and uses these commands:

```python
from config.simple_commands import SIMPLE_COMMANDS
from utils.command_normalization import find_matching_command

# Check if user input matches a simple command
matched = find_matching_command(user_input, SIMPLE_COMMANDS)
if matched:
    # Execute directly without LLM classification
    execute_action(matched)
```
