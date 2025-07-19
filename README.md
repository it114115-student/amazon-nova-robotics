# Amazon Nova Robotics

A comprehensive voice-controlled robotics platform powered by AWS IoT, AWS Bedrock, and Amazon Nova. This project enables natural language control of humanoid robots and drones through voice commands, with real-time 3D visualization and simulation capabilities.

## 🎯 Project Overview

Amazon Nova Robotics is a multi-component system that combines:

- **Voice Control**: Real-time speech-to-speech interaction using Amazon Nova Sonic
- **Robot Control**: Physical humanoid robot and drone control via AWS IoT
- **3D Simulation**: Browser-based 3D robot simulator with realistic animations
- **Text Interface**: Web-based text control for robot commands
- **MCP Integration**: Model Context Protocol support for extensibility

## 🏗️ Architecture

The system consists of several interconnected components:

### Core Components

1. **Speech Control** (`speech_control/`)

   - Real-time audio streaming with Amazon Nova Sonic
   - WebSocket-based bidirectional communication
   - MCP (Model Context Protocol) integration for extensibility
   - TypeScript/Node.js backend with web interface

2. **Humanoid Robot Simulator** (`humanoid-robot-simulator/`)

   - 3D web interface with Six.js visualization
   - 6 humanoid robots with 44 realistic actions
   - Real-time WebSocket communication
   - Python Flask backend with comprehensive API

3. **Text Control** (`text_control/`)

   - Web-based text interface for robot control
   - Python Flask application with AWS Bedrock integration
   - Database-backed session management

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

### Tech Blog

[Voice-Controlled Humanoid Robots Using Amazon Nova Sonic and AWS IoT](https://community.aws/content/2vqYxQLMJ8dYsL9kJnfPj0wIps3/voice-controlled-humanoid-robots-using-amazon-nova-sonic-and-aws-iot)

## 🚀 Quick Start

### Prerequisites

- Node.js 22+ (for speech control)
- Python 3.8+ (for simulators and robot clients)
- AWS CLI configured with appropriate permissions
- Docker (optional, for containerized deployment)

### Environment Setup

#### Update Node.js to version 22

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.2/install.sh | bash
```

Close the terminal and reopen, then:

```bash
nvm use 22
nvm alias default 22
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

```bash
cdk deploy --require-approval never --outputs-file output.json
```

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

## 🤖 Component Usage

### 1. Speech Control Interface

Navigate to the deployed speech control URL or run locally:

```bash
cd speech_control
npm install
npm run dev
```

Access at `http://localhost:3000`

Features:

- Real-time voice interaction with Amazon Nova Sonic
- Multi-robot selection and control
- WebSocket-based audio streaming
- MCP tool integration

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
- 44 different actions (dance, combat, exercise, movement)
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

- Text-based robot commands
- AWS Bedrock integration
- Session management
- Database-backed history

### 4. Physical Robot Deployment

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
- **Group Control**: Use `"all"` to control all robots simultaneously

### MCP Integration

The speech control component includes Model Context Protocol support for extensibility. Configure MCP servers in `speech_control/mcp_config.json`:

```json
{
  "mcpServers": {
    "server-name": {
      "command": "command-to-run",
      "args": ["arg1", "arg2"],
      "disabled": false,
      "autoApprove": ["tool1", "tool2"]
    }
  }
}
```

## 📊 Monitoring and Management

### API Endpoints

- **Speech Control**: `/api/mcp/status`, `/api/tools`
- **Robot Simulator**: WebSocket API for real-time control
- **Text Control**: RESTful API for command execution

### Session Management

Each component supports session-based interaction:

- Speech sessions with automatic cleanup
- Simulator sessions with multi-user support
- Text sessions with persistent history

## 🔒 Security

- AWS IAM roles and policies for least-privilege access
- IoT device certificates for secure communication
- Session-based authentication
- CORS configuration for web interfaces

## 🧩 Component Details

### Speech Control

- **Technology**: TypeScript, Node.js, Express, Socket.IO
- **Features**: Real-time audio streaming, MCP integration, multi-robot control
- **AI Model**: Amazon Nova Sonic for speech-to-speech processing
- **Deployment**: AWS App Runner with auto-scaling

### Humanoid Robot Simulator

- **Technology**: Python Flask, Three.js, WebSocket
- **Features**: 6 robots, 44 actions, 3D visualization, session management
- **Actions**: Dance (10 styles), Combat, Exercise, Movement
- **Deployment**: Docker-ready, Cloud Run compatible

### Text Control

- **Technology**: Python Flask, AWS Bedrock
- **Features**: Text-based commands, session history, database integration
- **Deployment**: AWS Lambda with API Gateway

### Robot Client

- **Technology**: Python, AWS IoT SDK, MQTT
- **Features**: Physical robot control, action execution, certificate-based auth
- **Hardware**: Humanoid robots and drones

### MCP Server

- **Technology**: Python, AWS Lambda
- **Features**: Model Context Protocol implementation, robot/drone commands
- **Integration**: Extensible tool system

### Infrastructure (CDK)

- **Services**: App Runner, Lambda, IoT Core, DynamoDB, S3
- **Features**: Auto-scaling, monitoring, secure networking
- **Region**: Primary deployment in us-east-1

## 🎮 Available Actions

### Humanoid Robot Actions (44 total)

#### Dance Actions (10 styles, 52-85 seconds each)

- `dance_1` through `dance_10`
- Professional choreographed sequences
- Music-synchronized movements

#### Combat Actions

- `kung_fu`, `wing_chun_form`, `kick`, `punch`, `uppercut`
- Martial arts sequences with proper stances

#### Exercise Actions

- `push_up`, `sit_up`, `squat`, `weightlifting`, `chest_exercise`
- Realistic exercise movements with proper form

#### Movement Actions

- `move_forward`, `move_backward`, `turn_left`, `turn_right`
- `fast_forward`, `fast_backward`, `fast_turn_left`, `fast_turn_right`

#### Basic Actions

- `wave`, `bow`, `jump`, `celebrate`, `think`
- `standing_1`, `standing_2`, `standing_3`

### Drone Actions

- `takeoff`, `land`, `move_up`, `move_down`
- `move_left`, `move_right`, `move_forward`, `move_back`
- `rotate_clockwise`, `rotate_counter_clockwise`

## 🔗 Integration Points

### AWS Services

- **Bedrock**: AI model inference and streaming
- **IoT Core**: Device communication and management
- **Lambda**: Serverless compute for MCP and text control
- **DynamoDB**: Session and robot state storage
- **S3**: Certificate and asset storage
- **App Runner**: Containerized web application hosting

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

- **Concurrent Sessions**: Supports multiple simultaneous voice sessions
- **Robot Capacity**: Up to 9 humanoid robots + drones per deployment
- **Auto-scaling**: Automatic scaling based on demand
- **Session Cleanup**: Automatic cleanup of inactive sessions (5-minute timeout)

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
3. Advanced MCP tool integrations
4. Multi-language support for voice commands
5. Robot fleet management interface
6. Performance analytics and monitoring
7. Mobile application development
