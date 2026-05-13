---
name: digital_human_adb
description: Control xiaoice Digital Human speech via MCP server and direct ADB. This version is for local network control.
---

# Digital Human ADB Skill

Controls the xiaoice Digital Human through BOTH direct ADB commands (local network) and the MCP server.

This version is optimized for scenarios where the Android device is in the same local network as the skill executor. It triggers the chat UI via ADB while simultaneously sending the speech message to AWS IoT via the MCP server.

## Prerequisites

- AWS CLI profile configured: `aws configure --profile <name>`
- MCP server deployed with `xiaoice_speech` tool
- Android device accessible via ADB on the local network
- `adb` installed on the host machine
- `settings.yaml` configured with the correct `adb_ip`

## Usage

```bash
# Send a speech message (triggers ADB flow and IoT)
./run.sh --message "Hello, welcome to the exhibition"

# Chinese message
./run.sh --message "歡迎嚟到我哋嘅展覽"
```

## Configuration

Edit `settings.yaml` in this directory:

```yaml
adb_ip: "192.168.137.211:5555"
adb_path: "adb" # or full path to adb
wait_duration: 2
```

## How It Works

1. The skill loads ADB settings from `settings.yaml`.
2. It attempts to connect to the Android device via `adb connect`.
3. It executes a UI flow:
   - Tap "Open chat" (1900, 775)
   - Tap "Close chat" (1650, 2275)
   - Wait `wait_duration` seconds
   - Tap "Open chat" again (1900, 775)
4. Simultaneously (sequentially in this script), it calls the `xiaoice_speech` MCP tool:
   - Saves message to DynamoDB
   - Publishes to `xiaoice_1/topic` IoT topic

## Troubleshooting

Ensure `adb` is in your PATH or configured correctly in `settings.yaml`. You can test connection manually:
```bash
adb connect 192.168.137.211:5555
adb devices
```
