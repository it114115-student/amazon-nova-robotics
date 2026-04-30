---
name: digital_human
description: Control xiaoice Digital Human speech via MCP server. Send text messages for the Digital Human to speak aloud through AWS IoT.
---

# Digital Human Skill

Controls the xiaoice Digital Human through the MCP server (Lambda function URL with SigV4 auth). Sends speech messages that are saved to DynamoDB and published to the xiaoice IoT topic.

There is only one xiaoice device (`xiaoice_1`), so no device ID is needed. The presenter context is handled automatically — all messages are saved and queried under a fixed key (`current_presenter`).

## Prerequisites

- AWS CLI profile configured: `aws configure --profile <name>`
- MCP server deployed with xiaoice_speech tool
- SpeechTable DynamoDB table provisioned (via CDK deploy)

## Usage

```bash
# Send a speech message
./run.sh --message "Hello, welcome to the exhibition"

# Chinese message
./run.sh --message "歡迎嚟到我哋嘅展覽"

# JSON output (for agent consumption)
./run.sh --message "Hello" --json
```

## How It Works

1. The skill calls the `xiaoice_speech` MCP tool via the Lambda function URL
2. The MCP server saves the message to the SpeechTable (DynamoDB) under `current_presenter`
3. The MCP server publishes the message to the `xiaoice_1/topic` IoT topic
4. The xiaoice client device receives the message and triggers the speech UI
5. The xiaoice welcome endpoint retrieves the latest pending message from `current_presenter`

## Troubleshooting

If `run.sh` fails, ensure dependencies are installed in the local virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
