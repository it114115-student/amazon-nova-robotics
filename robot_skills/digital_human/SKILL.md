---
name: digital_human
description: Control xiaoice Digital Human speech via MCP server. Send text messages for the Digital Human to speak aloud through AWS IoT.
---

# Digital Human Skill

Controls the xiaoice Digital Human through the MCP server (Lambda function URL with SigV4 auth). Sends speech messages that are saved to DynamoDB and published to the xiaoice IoT topic.

## Prerequisites

- AWS CLI profile configured: `aws configure --profile <name>`
- MCP server deployed with xiaoice_speech tool
- SpeechTable DynamoDB table provisioned (via CDK deploy)

## Usage

```bash
# Send a speech message
./run.sh --xiaoice-id xiaoice_1 --message "Hello, welcome to the exhibition"

# Send speech with a presenter context
./run.sh --xiaoice-id xiaoice_1 --message "Welcome everyone" --presenter-id Summer

# Send to all xiaoice devices
./run.sh --xiaoice-id all --message "The show is starting"

# JSON output (for agent consumption)
./run.sh --xiaoice-id xiaoice_1 --message "Hello" --json

```

## Supported Devices

xiaoice_1, all

## How It Works

1. The skill calls the `xiaoice_speech` MCP tool via the Lambda function URL
2. The MCP server saves the message to the SpeechTable (DynamoDB)
3. The MCP server publishes the message to the `xiaoice_*/topic` IoT topic
4. The xiaoice client device receives the message and triggers the speech UI

## Troubleshooting

If `run.sh` fails, ensure dependencies are installed in the local virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
