# Robot Skills

Self-contained, independently runnable robot control skills for AWS IoT.

## Prerequisites

- Python 3.8+
- AWS CLI configured with a named profile: `aws configure --profile <profile-name>`

## Skills

| Skill | Description |
|---|---|
| `humanoid_skill` | Publish actions to humanoid robots (robot_1 through robot_9) |
| `digital_human` | Send speech actions to the xiaoice Digital Human via AWS IoT |
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

Each python skill script automatically detects either `MCP_SERVER_URL` or `McpServerUrl` environment variables. If you have deployed your CDK stacks, you can load the environment variables directly from the CDK output before running any skill:

```bash
# From the project root directory
source load_cdkstack_env.sh

# Now run the skill directly, it will seamlessly route requests through the AWS Bedrock AgentCore Secure Gateway
cd robot_skills/humanoid
./run.sh --robot-id robot_1 --action wave
```

Each skill is fully independent — its own venv, its own deps, no shared imports.
