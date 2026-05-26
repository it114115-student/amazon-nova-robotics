# AWS Cloud System Architecture & Design Specification

This document provides a unified, comprehensive overview of the AWS Cloud Serverless architecture powering the **Amazon Nova Robotics** ecosystem. This system integrates real-time humanoid voice control (powered by **Amazon Bedrock AgentCore Runtime** and **Amazon Nova Sonic**) and the gesture-controlled **Domain Expansion AR Game** (powered by **AWS API Gateway**, **DynamoDB**, and **AWS Lambda**).

---

## 🏗️ Unified AWS System Design Diagram

The following diagram illustrates the complete end-to-edge cloud infrastructure, detailing how static web assets, secure federated user credentials, real-time audio streams, split API routes, asynchronous queue workers, and physical IoT commands interact:

```mermaid
graph TB
    subgraph Client Layer ["Client Tier (Browser & Devices)"]
        BrowserVoice["Voice Chat Client (v1.0.11)"]
        BrowserGame["Domain Expansion Web (AR Game)"]
        ThreeJSSim["Humanoid Simulator (Three.js)"]
    end

    subgraph CDN Layer ["Global CDN & Edge Delivery"]
        CFVoice["CloudFront CDN (Voice Web)"]
        CFGame["CloudFront CDN (Game Web)"]
        CFSim["CloudFront CDN (Simulator Web)"]
        S3Voice[("S3 Bucket: Voice Web")]
        S3Game[("S3 Bucket: Game Web")]
        S3Sim[("S3 Bucket: Simulator Web")]
    end

    subgraph Security Layer ["Identity & Authorization"]
        CognitoPool["Cognito User Pool (User Directory)"]
        CognitoIdent["Cognito Identity Pool (IAM Credentials)"]
    end

    subgraph Interface Layer ["API Routing & Signaling Gateway"]
        APIGatewayREST["API Gateway REST HTTP API"]
        APIGatewayWS["API Gateway WebSocket API"]
        BedrockAgentRuntime["Bedrock AgentCore Gateway (SigV4)"]
    end

    subgraph Computing Layer ["Serverless Computing & Orchestration"]
        LambdaGame["Lambda Handler (Python Game Backend)"]
        SQSGame[("Amazon SQS (Image Fusion Queue)")]
        LambdaWorker["Lambda Worker (Bedrock Image Fusion)"]
        FastAPIAgent["FastAPI Container (AgentCore Voice Runtime)"]
    end

    subgraph AI Model Layer ["AWS AI Foundation Models"]
        NovaSonic["Amazon Nova Sonic (Voice Synth)"]
        BedrockImage["Amazon Bedrock (Canvas Image Generation)"]
    end

    subgraph Database Layer ["DynamoDB Storage & State Engine"]
        DDBGame[("DynamoDB: Game & Snapshot Sessions")]
        DDBRobots[("DynamoDB: Robot Configuration & Joints")]
    end

    subgraph IoT Layer ["Robotics Fleet Management"]
        IoTCore["AWS IoT Core (MQTT Message Broker)"]
        PhysicalRobots["Physical Fleet (Humanoids & Drones)"]
    end

    %% Web Asset Hosting Links
    CFVoice --> S3Voice
    CFGame --> S3Game
    CFSim --> S3Sim
    BrowserVoice -->|Pulls Static Assets| CFVoice
    BrowserGame -->|Pulls Static Assets| CFGame
    ThreeJSSim -->|Pulls Static Assets| CFSim

    %% Authentication & Authorization Links
    BrowserVoice -->|1. Sign In / Authenticate| CognitoPool
    BrowserVoice -->|2. Exchange Token| CognitoIdent
    CognitoIdent -->|3. Temporary IAM SigV4 Credentials| BrowserVoice
    BrowserGame -->|Sign In / Authenticate| CognitoPool

    %% Voice Web Routing Links
    BrowserVoice -->|4. Handshake with IAM SigV4| BedrockAgentRuntime
    BedrockAgentRuntime -->|5. Connects Bidirectional WebSocket| FastAPIAgent
    FastAPIAgent -->|6. Low-latency Voice Synth (PCM_16)| NovaSonic
    FastAPIAgent -->|7. Invoke MCP Tools| LambdaGame

    %% Game REST API Routes (Split Public/Private)
    BrowserGame -->|GET /api/get-snapshot (Public NONE)| APIGatewayREST
    BrowserGame -->|GET /api/last-image (Public NONE)| APIGatewayREST
    BrowserGame -->|POST /api/enhance-portrait (Secure COGNITO)| APIGatewayREST
    BrowserGame -->|Other HTTP Actions (Secure COGNITO)| APIGatewayREST
    APIGatewayREST --> LambdaGame

    %% Game WebSocket Signaling (Secure)
    BrowserGame -->|Handshake with Token (Secure COGNITO)| APIGatewayWS
    APIGatewayWS --> LambdaGame

    %% Image Fusion Pipeline
    LambdaGame -->|Enqueue Image Requests| SQSGame
    SQSGame --> LambdaWorker
    LambdaWorker -->|Generate Image Fusion| BedrockImage
    LambdaWorker -->|Update Snapshot Status| DDBGame

    %% Database Queries
    LambdaGame --> DDBGame
    LambdaGame --> DDBRobots
    FastAPIAgent --> DDBRobots

    %% IoT Routing Links
    LambdaGame -->|Publish Joint State MQTT Command| IoTCore
    IoTCore -->|MQTT Sync| PhysicalRobots
    IoTCore -->|MQTT Sync| ThreeJSSim
```

---

## 🎙️ Speech Control (Voice Web) Architectural Specifications

The Speech Control Cockpit is a high-performance, real-time voice streaming control interface powered by **Amazon Nova Sonic**.

### 1. Unified Authentication Protocol
* **The Flow**:
  1. The user logs in via a web interface (`/login.html`) against an **AWS Cognito User Pool**.
  2. The browser exchanges the Cognito Identity Token with an **AWS Cognito Identity Pool**.
  3. The Identity Pool vends short-lived, temporary AWS IAM credentials.
  4. The browser utilizes these credentials to cryptographically generate an **AWS Signature Version 4 (SigV4)** pre-signed handshake URL.
  5. The browser opens a secure WebSocket connection directly with the **AWS Bedrock AgentCore API Gateway** boundary.
* **Security Benefit**: Zero AWS secrets are stored on the frontend, and no custom middleware server is needed to sign connections. Authentications are handled entirely at the AWS Cloud frontier.

### 2. Live2D Real-time Lip-Sync Processing Engine (`v1.0.11`)
Standard Web Audio implementations often suffer from security limits, such as browsers suspending the active `AudioContext` until a manual user gesture occurs. To ensure perfect, bulletproof lip-syncing, we implemented an event-driven blending audio loop:

1. **Direct WebSocket RMS Extraction**:
   Upon receiving raw WebSocket audio streaming chunks (`audioOutput` event), the client immediately decodes the binary 16-bit PCM (`PCM_16`) array on the main loop and computes the raw **Root Mean Square (RMS)** amplitude:
   $$\text{rms} = \sqrt{\frac{1}{N}\sum_{i=1}^N \text{pcm}[i]^2}$$
   This RMS value is pushed instantly to the audio player via `audioPlayer.setWebSocketVolume(rms)`.

2. **Decay Envelope Tracking**:
   In `AudioPlayer.js`, a decay filter tracking variable (`websocketVolume`) is updated on each frame. If no new packets are received within $120\text{ms}$, the volume smoothly decays down to zero to close the mouth naturally:
   ```javascript
   if (elapsedTime > 120) {
       this.websocketVolume *= 0.85;
   }
   ```

3. **Multi-Source Audio Blending**:
   The Live2D Avatar update loop fetches the volume by blending speaker playback volumes and WebSocket packet volumes:
   $$\text{volume} = \max(\text{speakerVolume}, \text{websocketVolume})$$
   * **Result**: The avatar's mouth is **guaranteed to move instantly** when speech data arrives over the network, completely bypassing browser audio suspension limitations.
   * **Console Debugging**: Includes a real-time throttled console logger showing active calculations:
     `[Live2D Mouth Sync Debug] rawVolume=0.0384, targetMouthOpen=0.1075, smoothedVolume=0.0892`

---

## 🎮 Domain Expansion Game Architectural Specifications

The JJK Domain Expansion AR Game incorporates high-fidelity hand sign gesture recognition using MediaPipe and interacts serverlessly with the AWS Cloud.

### 1. Secure Split-Routing REST Architecture
To deliver a secure game that perfectly integrates with native browser media elements (which cannot attach custom HTTP bearer authorization headers), we designed a **split-route API Gateway Rest API**:

* 🔒 **Cognito Protected Endpoints (Catch-All Proxy `/{proxy+}`)**:
  * Critical HTTP methods like `/api/enhance-portrait` (triggering expensive Bedrock Canvas style fusions), `/api/register-room`, `/api/live-status`, and `/api/battle-result` are proxy-mapped to the AWS Lambda backend.
  * They are protected by an **API Gateway Cognito User Pools Authorizer**. If the client request lacks a valid Cognito bearer token, API Gateway drops the query instantly with a `401 Unauthorized` response.
* 🔓 **Public Media Access (`/api/get-snapshot` & `/api/last-image`)**:
  * Because standard browser HTML image elements (e.g., `<img src="...">`) fetch images natively and cannot append custom authorization headers, protecting image retrievals with Cognito would prevent pictures from loading.
  * We explicitly defined these two read-only endpoints as **explicit API Gateway resources** with `AuthorizationType.NONE`.
  * Because they are read-only and require a valid, secret `sessionId` (e.g., `"mcpserver"`) to locate the snapshot, they are completely safe from malicious exploits while allowing images to render flawlessly.

### 2. High-Performance Battle Mode Real-Time Sync
* **WebRTC P2P Signaling**: 
  The game supports local and online multiplayer modes. In online mode, browsers establish a secure, encrypted peer-to-peer **WebRTC** connection to stream user camera views directly between players' screens.
* **WebSocket Signaling**:
  The game's Socket.io / API Gateway WebSocket connection acts only as a lightweight room coordination signaling switchboard. It handles only game coordinates, technique triggers, and score broadcasts (never seeing camera streams), saving maximum cloud bandwidth and keeping latencies minimal.

### 3. Consolidated `"mcpserver"` Default Session Key
* **Standardization**: Both frontend elements ([battle.js](file:///home/developer/Documents/data-disk/amazon-nova-robotics/domain-expansion-ar-game/static/js/battle.js), [hand_tracker.js](file:///home/developer/Documents/data-disk/amazon-nova-robotics/domain-expansion-ar-game/static/js/hand_tracker.js)) and cloud backend components ([lambda_function.py](file:///home/developer/Documents/data-disk/amazon-nova-robotics/domain-expansion-ar-game-serverless/backend/lambda_function.py), [image_processor.py](file:///home/developer/Documents/data-disk/amazon-nova-robotics/domain-expansion-ar-game-serverless/backend/image_processor.py), [commentary.py](file:///home/developer/Documents/data-disk/amazon-nova-robotics/domain-expansion-ar-game-serverless/backend/commentary.py)) default to a standard `"mcpserver"` session ID.
* This ensures that any battles fought, snapshots captured, or commentaries generated are seamlessly integrated and accessible by your conversational agents.
