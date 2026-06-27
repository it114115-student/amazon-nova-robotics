# Robot Skills

Self-contained, independently runnable skills for the Bedrock AgentCore gateway-backed robot and digital-human toolchain.

## Prerequisites

- Python 3.8+
- AWS CLI configured with a named profile: `aws configure --profile <profile-name>`

## Skills

| Skill | Description |
|---|---|
| `humanoid_skill` | Invoke humanoid robot actions, speech, and image capture through the robot-only AgentCore gateway target |
| `digital_human` | Send speech actions to the xiaoice Digital Human through the digital-human AgentCore gateway target |
| `digital_human_adb` | Control local/connected Android devices for Digital Human live2d/application display via ADB |

## Usage

```bash
cd <skill_folder>

# With named profile
./run.sh --profile my-aws-profile --robot-id robot_1 --action wave

# Uses 'default' profile if --profile is omitted
./run.sh --robot-id robot_1 --action wave
```

### CDK Environment Variables Integration (Recommended)

Each Python skill script automatically detects either `MCP_SERVER_URL` or `McpServerUrl`. If you have deployed the CDK stack, `load_cdkstack_env.sh` exports the `McpServerUrl` output so the skills can talk to the AgentCore gateway without extra configuration:

```bash
# From the project root directory
source load_cdkstack_env.sh

# Now run the skill directly; it will route requests through the Bedrock AgentCore gateway
cd robot_skills/humanoid
./run.sh --robot-id robot_1 --action wave
```

Each skill is fully independent — its own venv, its own deps, no shared imports.
