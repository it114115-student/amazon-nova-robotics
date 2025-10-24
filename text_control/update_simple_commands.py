#!/usr/bin/env python3
"""
Extract robot commands from MCP server tools.
This script looks for @mcp.tool() decorated functions and extracts action
names.
"""

import re
from pathlib import Path


def extract_commands_from_mcp_tools():
    """Extract commands from MCP server tools by analyzing @mcp.tool()
    functions."""

    # Get the MCP server path
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    mcp_server_path = project_root / "mcp_server" / "tools"

    all_commands = set()

    if not mcp_server_path.exists():
        print(f"MCP server tools not found at: {mcp_server_path}")
        return all_commands

    print(f"Scanning MCP tools at: {mcp_server_path}")

    for tool_file in mcp_server_path.glob("*.py"):
        print(f"\nAnalyzing {tool_file.name}...")

        try:
            with open(tool_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Extract commands from this file
            file_commands = extract_commands_from_content(content)

            if file_commands:
                print(
                    f"  Found {len(file_commands)} commands: "
                    f"{sorted(file_commands)}"
                )
                all_commands.update(file_commands)
            else:
                print("  No commands found")

        except (FileNotFoundError, IOError, OSError) as e:
            print(f"  Error reading {tool_file}: {e}")

    return all_commands


def extract_commands_from_content(content):
    """Extract action names from execute_*_action calls in @mcp.tool()
    functions."""
    commands = set()

    # Pattern to match @mcp.tool() functions and capture their content
    # This matches from @mcp.tool() to the next @mcp.tool() or end of function
    tool_pattern = (
        r"@mcp\.tool\(\)\s*def\s+\w+.*?"
        r"(?=@mcp\.tool\(\)|def\s+register_|$)"
    )

    tool_functions = re.findall(tool_pattern, content, re.DOTALL)

    for func_content in tool_functions:
        # Look for various execute action patterns within each @mcp.tool()
        # function
        patterns = [
            # execute_dog_action(dog_id, "action_name", {})
            r'execute_dog_action\s*\([^,]+,\s*["\']([^"\']+)["\']',
            # execute_action("action_name")
            r'execute_action\s*\(\s*["\']([^"\']+)["\']',
            # execute_drone_action(drone_id, "action_name", {})
            r'execute_drone_action\s*\([^,]+,\s*["\']([^"\']+)["\']',
            # execute_robot_action(robot_id, "action_name", {})
            r'execute_robot_action\s*\([^,]+,\s*["\']([^"\']+)["\']',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, func_content)
            commands.update(matches)

    return commands


def update_simple_commands_file(commands):  # pylint: disable=too-many-branches
    """Update the simple_commands.py file with extracted commands."""

    if not commands:
        print("No commands found to update.")
        return

    # Basic categorization
    categories = {
        "basic": set(),
        "movement": set(),
        "look": set(),
        "advanced": set(),
        "other": set(),
    }

    for cmd in commands:
        if cmd in ["stop", "activate", "stand", "sit", "bow", "wave", "hop"]:
            categories["basic"].add(cmd)
        elif any(
            word in cmd
            for word in [
                "move", "turn", "step", "rotate", "walk", "run", "jump"
            ]
        ):
            categories["movement"].add(cmd)
        elif "look" in cmd:
            categories["look"].add(cmd)
        elif any(
            word in cmd
            for word in [
                "head",
                "body",
                "leg",
                "height",
                "balance",
                "gait",
                "cycle",
                "ellipse",
            ]
        ):
            categories["advanced"].add(cmd)
        else:
            categories["other"].add(cmd)

    # Generate the file content
    content = '''"""
Simple commands configuration for robot control.
This file contains the set of commands that don't require LLM classification.
Auto-generated from MCP server analysis.
"""

# Simple commands that don't need classification
SIMPLE_COMMANDS = {
'''

    if categories["basic"]:
        content += "    # Basic control commands\n"
        for cmd in sorted(categories["basic"]):
            content += f'    "{cmd}",\n'

    if categories["movement"]:
        content += "    # Movement commands\n"
        for cmd in sorted(categories["movement"]):
            content += f'    "{cmd}",\n'

    if categories["look"]:
        content += "    # Look/Vision commands\n"
        for cmd in sorted(categories["look"]):
            content += f'    "{cmd}",\n'

    if categories["advanced"]:
        content += "    # Advanced commands\n"
        for cmd in sorted(categories["advanced"]):
            content += f'    "{cmd}",\n'

    if categories["other"]:
        content += "    # Other commands\n"
        for cmd in sorted(categories["other"]):
            content += f'    "{cmd}",\n'

    content += "}\n"

    # Write to file
    output_path = (
        Path(__file__).parent / "command_config" / "simple_commands.py"
    )
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"\nUpdated {output_path}")

    # Show summary
    total = sum(len(cmds) for cmds in categories.values())
    print(f"Total commands: {total}")
    for category, cmds in categories.items():
        if cmds:
            print(f"  {category}: {len(cmds)}")


def main():
    """Main function."""
    print("Extracting commands from MCP server tools...")

    commands = extract_commands_from_mcp_tools()

    if commands:
        print(f"\nTotal unique commands found: {len(commands)}")
        print(f"Commands: {sorted(commands)}")
        update_simple_commands_file(commands)
    else:
        print("No commands found!")


if __name__ == "__main__":
    main()
