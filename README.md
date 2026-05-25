# Amazon Nova Robotics

A comprehensive voice-controlled robotics platform powered by AWS IoT, AWS Bedrock, and Amazon Nova. This project enables natural language control of humanoid robots and drones through voice commands, with real-time 3D visualization, simulation capabilities, and secure authentication.

## 📚 Documentation

See the consolidated documentation index in [docs/README.md](docs/README.md).

## 🎯 Project Overview

Amazon Nova Robotics is a multi-component system that combines:

- **Voice Control**: Real-time speech-to-speech interaction using Amazon Nova Sonic
- **Robot Control**: Physical humanoid robot and drone control via AWS IoT
- **3D Simulation**: Browser-based 3D robot simulator with realistic animations
- **Text Interface**: Web-based text control for robot commands
- **MCP Integration**: Model Context Protocol support for extensibility
- **Authentication**: AWS Cognito-based user authentication for secure access

## 🏗️ Architecture

The system consists of several interconnected components:

### Core Components

1. **Speech Control** (`speech_control_agentcore/`)

   - Real-time, bidirectional voice-to-voice streaming with Amazon Nova Sonic
   - Serverless AWS Bedrock AgentCore WebSocket Runtime connection patterns
   - Serverless static browser frontend hosted on Amazon S3 behind a CloudFront CDN
   - Direct browser-based IAM SigV4 authenticated WebSocket handshake signatures
   - Real-time dynamic system prompt adaptation matching selected hardware devices
   - Fluid, zero-refresh reconnection state machine and microphonic resource cleanup

2. **Humanoid Robot Simulator** (`humanoid-robot-simulator/`)

   - 3D web interface with Three.js visualization
   - 6 humanoid robots with 38 realistic actions
   - Real-time WebSocket communication
   - Python Flask backend with comprehensive API

3. **Text Control** (`text_control/`)

   - Web-based text interface for robot control
   - Python Flask application with AWS Bedrock integration
   - Database-backed session management
   - AWS Cognito authentication integration
   - Command optimization system for faster response

4. **Robot Client** (`robot_client/`)

   - Physical robot control software
   - AWS IoT MQTT communication
   - Support for humanoid robots and drones
   - Python-based with action execution system

5. **MCP Server** (`mcp_server/`)

   - Model Context Protocol server implementation
   - Robot and drone command execution
   - AWS Lambda-based deployment

6. **CDK Infrastructure** (`cdk/`)
   - AWS Cloud Development Kit deployment scripts
   - Complete AWS infrastructure provisioning
   - Auto-scaling and monitoring configuration

7. **Domain Expansion AR Game** (`domain-expansion-ar-game/`)
   - Standalone AR experience using MediaPipe hand tracking
   - JJK-themed gesture control for robots
   - No WebSocket required for standalone mode

### Tech Blog

[Voice-Controlled Humanoid Robots Using Amazon Nova Sonic and AWS IoT](https://community.aws/content/2vqYxQLMJ8dYsL9kJnfPj0wIps3/voice-controlled-humanoid-robots-using-amazon-nova-sonic-and-aws-iot)

## 🚀 Quick Start

### Prerequisites

- Node.js 23+ (for speech control)
- Python 3.8+ (for simulators and robot clients)
- AWS CLI configured with appropriate permissions
- Docker (optional, for containerized deployment)

### Environment Setup

#### Update Node.js to version 23

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.2/install.sh | bash
```

Close the terminal and reopen, then:

```bash
nvm install 23
nvm use 23
nvm alias default 23
```

#### Install and Update CDK

```bash
cd cdk
pip install --upgrade awscli
npm uninstall -g cdk
npm install -g cdk
npm i -g npm-check-updates && ncu -u && npm i
```

#### Configure AWS CLI

```bash
aws configure
```

- Default region name: `us-east-1`
- Default output format: `json`

## 🏗️ Infrastructure Deployment

### Deploy AWS Infrastructure

1. **CDK Bootstrap** (first time only):

```bash
cd cdk
cdk bootstrap
```

2. **Deploy Stacks**:
   Install jq, if you don't have it.

```bash
sudo apt update && sudo apt install -y jq
```

> [!IMPORTANT]
> **ARM64 Emulation inside GitHub Codespaces / AMD64 Environments**
> 
> The AWS Bedrock AgentCore containers are built for **ARM64** architecture (`Platform.LINUX_ARM64`). If you deploy from an **AMD64/x86_64** host (like standard GitHub Codespaces):
> 1. The `./deploy.sh` script is fully automated and will try to install native host emulation using:
>    ```bash
>    sudo apt-get update && sudo apt-get install -y qemu-user-static binfmt-support
>    ```
> 2. If native installation is not supported by your host OS, the script will automatically fallback to registering emulation via a privileged binfmt Docker container.
> 3. Ensure Docker is running in your development environment before executing the deployment script.

Deployment

```bash
./deploy.sh
```

This script will:

- Deploy the CDK stack
- Automatically sync IoT certificates from S3 to local robot_client/certificates/

3. **Destroy Stacks** (when needed):

```bash
cdk destroy --require-approval never
```

### Local Development Setup

#### Load Environment Variables

```bash
sudo apt update && sudo apt install -y jq
source /workspaces/amazon-nova-robotics/load_cdkstack_env.sh
```

#### Download AWS IoT Certificates

```bash
source load_cdkstack_env.sh
aws s3 sync s3://$RobotDataBucketName robot_client/certificates/
```

#### Create Test Users (for authentication)

You can easily register or create test users directly inside your AWS Cognito User Pool via the AWS CLI:

```bash
aws cognito-idp admin-create-user \
  --user-pool-id $CognitoUserPoolId \
  --username testuser \
  --user-attributes Name=email,Value=testuser@example.com
```

## 🤖 Component Usage

### 1. Speech Control Interface

The serverless Speech Control frontend is served globally via AWS CloudFront. To run components locally for development:

**Run the Backend Agent Service:**
```bash
cd speech_control_agentcore
pip install -r requirements.txt
python robot_voice_agent.py
```

**Serve the Frontend Website Static Assets:**
```bash
cd speech_control_agentcore/public
python -m http.server 3000
```
Access the static developer interface at `http://localhost:3000`!

Features:

- Real-time voice interaction with Amazon Nova Sonic
- Multi-robot selection and control
- WebSocket-based audio streaming
- MCP tool integration
- Secure authentication with session management

### 2. Humanoid Robot Simulator

Access the 3D robot simulator:

```bash
cd humanoid-robot-simulator
pip install -r requirements.txt
python app.py
```

Access at `http://localhost:5000?session_key=YOUR_SESSION`

Features:

- 6 humanoid robots with realistic 3D models
- 38 different actions (dance, combat, exercise, movement)
- Real-time WebSocket updates
- Group control capabilities

### 3. Text Control Interface

Web-based text control:

```bash
cd text_control
pip install -r requirements.txt
python app.py
```

Features:

- Text-based robot commands with intelligent optimization
- AWS Bedrock integration for complex commands
- Session management with authentication
- Database-backed history
- 2-4 second performance improvement for simple commands

### 4. Domain Expansion AR Game

Interactive hand-gesture control system:

- **Live Demo**: [Play Now](https://wongcyrus.github.io/domain-expansion-ar-game/)
- **Setup**: Open `domain-expansion-ar-game/index.html` in a web browser.
- **Local Testing**: Run `python3 serve_https.py` in the directory for mobile testing.

Features:

- Real-time 21-point hand tracking via MediaPipe
- JJK-themed visual effects (Unlimited Void, Hollow Purple, etc.)
- Direct REST API communication with robots
- Interactive "Energy Ball" finger tracking

### 5. Physical Robot Deployment

For physical robot hardware:

1. **Generate deployment package**:

   ```bash
   ./create_deploy_package.sh
   ```

2. **Transfer to robot** and extract:

   ```bash
   unzip deploy_package.zip
   ```

3. **Configure robot settings**:
   Edit `settings.yaml` to specify `robot_name` (robot_1 through robot_9 supported)

4. **Setup and run**:
   ```bash
   ./create_virtual_env.sh
   source venv/bin/activate
   python pubsub.py
   ```

## 🔧 Configuration

### Robot Configuration

The system supports:

- **Humanoid Robots**: `robot_1` through `robot_9`
- **Drones**: `drone_1` and above
- **Dogs**: `dog_1` through `dog_3` (Raspberry Pi Dog controllers)
- **Group Control**: Use `"all"` to control all robots simultaneously

### MCP Integration

The serverless Bedrock AgentCore voice-agent architecture includes Model Context Protocol (MCP) support for serverless command routing:
- **Serverless MCP Routing**: The voice assistant routes tools directly via AWS Lambda. When the Bedrock agent decides to invoke an action (such as `robot_kick` or `robot_dance`), the MCP Lambda converts the payload and POSTs it directly to your CloudFront-backed humanoid robot simulator REST endpoint.
- **Zero-Touch Configuration**: All MCP tool schemas and routing targets are declared and wired natively inside your AWS CDK stack ([`cdk-stack.ts`](file:///home/developer/Documents/data-disk/amazon-nova-robotics/cdk/lib/cdk-stack.ts)), completely eliminating local file management for seamless, native serverless orchestrations!

The system supports AWS IAM authentication for secure MCP Lambda Function URLs.

## 📊 Monitoring and Management

### API Endpoints

- **Speech Control**: `/api/mcp/status`, `/api/tools`, `/api/auth/config`, `/api/auth/login`
- **Robot Simulator**: WebSocket API for real-time control
- **Text Control**: RESTful API for command execution with authentication
- **Authentication**: AWS Cognito integration for secure access

### Session Management

Each component supports session-based interaction with authentication:

- Speech sessions with automatic cleanup and Cognito authentication
- Simulator sessions with multi-user support and secure session keys
- Text sessions with persistent history and JWT token authentication

## 🔒 Security

- AWS IAM roles and policies for least-privilege access
- IoT device certificates for secure communication
- AWS Cognito authentication for web interfaces
- Session-based authentication with JWT tokens
- Socket.IO authentication middleware
- CORS configuration for web interfaces
- MCP server AWS SigV4 authentication support

## 🧩 Component Details

### Speech Control

- **Technology**: TypeScript, Node.js, Express, Socket.IO
- **Features**: Real-time audio streaming, MCP integration, multi-robot control, authentication
- **AI Model**: Amazon Nova Sonic for speech-to-speech processing
- **Authentication**: AWS Cognito with JWT tokens
- **MCP Support**: AWS SigV4 authentication for secure Lambda Function URLs
- **Deployment**: AWS App Runner with auto-scaling

### Humanoid Robot Simulator

- **Technology**: Python Flask, Three.js, WebSocket
- **Features**: 6 robots, 38 actions, 3D visualization, session management
- **Actions**: Dance (9 styles), Combat, Exercise, Movement
- **Deployment**: Docker-ready, Cloud Run compatible

### Text Control

- **Technology**: Python Flask, AWS Bedrock
- **Features**: Text-based commands, session history, database integration, command optimization
- **Performance**: 2-4 second speedup for simple commands, 5x faster multi-robot execution
- **Commands**: 43+ robot commands automatically extracted from MCP server
- **Deployment**: AWS Lambda with API Gateway

### Domain Expansion AR Game

- **Technology**: Vanilla JavaScript, MediaPipe, Canvas API
- **Features**: Real-time hand tracking, cinematic JJK VFX, bilingual UI (EN/ZH)
- **Controls**: 8+ Domain Expansions and 3+ hand techniques
- **Deployment**: Standalone static site, GitHub Pages ready

### Robot Client

- **Technology**: Python, AWS IoT SDK, MQTT
- **Features**: Physical robot control, action execution, certificate-based auth
- **Hardware**: Humanoid robots and drones

### MCP Server

- **Technology**: Python, AWS Lambda
- **Features**: Model Context Protocol implementation, robot/drone commands
- **Integration**: Extensible tool system

### Infrastructure (CDK)

- **Services**: App Runner, Lambda, IoT Core, DynamoDB, S3, Cognito
- **Features**: Auto-scaling, monitoring, secure networking, batch IoT processing
- **Efficiency**: 92.3% reduction in Lambda functions through batch IoT device creation
- **Devices**: Single Lambda handles all 13 IoT devices (9 robots + 1 drone + 3 dogs)
- **Region**: Primary deployment in us-east-1

## 🎮 Available Actions

### Humanoid Robot Actions (38 total)

#### Dance Actions (9 styles, 52-85 seconds each)

- `dance_two` through `dance_ten` (note: dance_one not implemented)
- Professional choreographed sequences
- Music-synchronized movements

#### Combat Actions

- `kung_fu`, `wing_chun`, `left_kick`, `right_kick`, `left_uppercut`, `right_uppercut`
- `left_shot_fast`, `right_shot_fast`
- Martial arts sequences with proper stances

#### Exercise Actions

- `push_ups`, `sit_ups`, `squat`, `squat_up`, `weightlifting`, `chest`
- Realistic exercise movements with proper form

#### Movement Actions

- `go_forward`, `back_fast`, `turn_left`, `turn_right`
- `left_move_fast`, `right_move_fast`, `stepping`
- Basic movement with directional control

#### Basic Actions

- `wave`, `bow`, `twist`, `stand`, `stand_up_back`, `stand_up_front`
- Basic interaction and positioning actions

### Drone Actions

- `takeoff`, `land`, `move_up`, `move_down`
- `move_left`, `move_right`, `move_forward`, `move_back`
- `rotate_clockwise`, `rotate_counter_clockwise`

## 🔗 Integration Points

### AWS Services

- **Bedrock**: AI model inference and streaming with Amazon Nova Sonic
- **IoT Core**: Device communication and management for robots and drones
- **Lambda**: Serverless compute for MCP and text control
- **DynamoDB**: Session and robot state storage
- **S3**: Certificate and asset storage
- **App Runner**: Containerized web application hosting
- **Cognito**: User authentication and session management

### Communication Protocols

- **WebSocket**: Real-time bidirectional communication
- **MQTT**: IoT device messaging
- **HTTP**: RESTful APIs and web interfaces
- **MCP**: Model Context Protocol for tool extensibility

## 🎯 Use Cases

1. **Educational Robotics**: Teaching programming and AI concepts
2. **Research Platform**: Testing voice-controlled robotics algorithms
3. **Entertainment**: Interactive robot demonstrations and performances
4. **Simulation**: Safe testing environment before physical deployment
5. **Development**: Rapid prototyping of robot behaviors and interactions

## 🐛 Troubleshooting

### Common Issues

1. **Session Connection Issues**

   - Verify WebSocket connectivity
   - Check session key validity
   - Ensure proper CORS configuration

2. **Robot Communication Problems**

   - Validate AWS IoT certificates
   - Check MQTT topic permissions
   - Verify robot naming convention

3. **MCP Tool Issues**
   - Check MCP server configuration
   - Verify tool auto-approval settings
   - Review server logs for connection errors

## 📈 Performance Considerations

- **Concurrent Sessions**: Supports multiple simultaneous voice sessions with authentication
- **Robot Capacity**: Up to 9 humanoid robots + 1 drone + 3 dogs per deployment (13 devices total)
- **Infrastructure Efficiency**: 92.3% reduction in Lambda functions through batch IoT processing
- **Auto-scaling**: Automatic scaling based on demand for App Runner services
- **Session Cleanup**: Automatic cleanup of inactive sessions (5-minute timeout)
- **Command Optimization**: Text control bypasses LLM for simple commands (2-4s speedup)
- **Simulator Capacity**: 6 humanoid robots in 3D visualization with 38 available actions

## 🛠️ Development

### Local Development

Each component can be developed independently with hot reload support.

### Testing

- Unit tests for core functionality
- Integration tests for WebSocket communication
- End-to-end tests for robot action execution

### Deployment Options

- **Local**: Direct execution on development machine
- **Docker**: Containerized deployment with docker-compose
- **AWS**: Full cloud deployment with CDK
- **Hybrid**: Cloud services with local robot clients

## 📋 TODO

1. Fine-grained AWS IoT device permissions
2. Enhanced robot action choreography
3. Multi-language support for voice commands
4. Robot fleet management interface
5. Mobile application development
6. Real-time performance analytics dashboard
7. Advanced MCP tool marketplace integration
8. Enhanced video streaming with computer vision
9. Multi-user collaboration features
10. Robot behavior learning and adaptation
