# Architecture Blog: Voice-Controlling a Humanoid Robotics Fleet with Amazon Bedrock AgentCore and Amazon Nova 2 Sonic

`[MARKER - UPLOAD COVER IMAGE: system_design/img/speech_control_blog_cover.png]`

**Published on:** June 17, 2026  
**Authors:** Senior Robotics Architect, AI/ML Specialist  
**Category:** Robotics, Artificial Intelligence, Voice-to-Speech, Serverless  
**Description:** Discover how to build a state-of-the-art, serverless voice cockpit to command humanoid robotics and quadcopter fleets using Amazon Bedrock AgentCore and Amazon Nova 2 Sonic. Learn how to pre-sign secure SigV4 WebSocket handshakes directly from the browser, eliminate health check log spam in FastAPI, orchestrate secure multi-agent Model Context Protocol (MCP) gateways, handle precise tool name extraction contracts within AWS Lambda, and animate real-time dual Live2D avatars with Web Audio Lip-Sync.

---

Modern robotics fleet operations require a quantum leap in user-interaction interfaces. Traditional joystick-and-keyboard control structures are highly rigid and demand extensive operator training. To build a more intuitive cockpit, we designed a **real-time voice-to-speech robotics fleet controller** that allows operators to command physical and simulated hardware fleets (including humanoid robots, drones, and digital humans) using natural spoken phrases.

Building a secure, low-latency, and zero-maintenance voice-control cockpit on traditional virtual machine fleets is incredibly expensive and complex. To achieve 100% serverless, zero-maintenance execution, we built **Speech Control AgentCore Cockpit** powered by **Amazon Bedrock AgentCore Runtime** and **Amazon Nova 2 Sonic**.

In this article, we reveal the detailed architecture, core CDK cloud formations, backend container implementations, and key engineering solutions we deployed to enable secure, bidirectional voice-control loops, multi-agent Model Context Protocol (MCP) orchestration, optimized logging configurations, and live avatar animations on AWS.

---

## High-Level Architecture Topology

The Speech Control Cockpit utilizes a serverless static frontend (React + HTML5 + Vanilla CSS) hosted on Amazon S3 and distributed via CloudFront. The backend voice agent runs inside a lightweight, stateless Docker container managed serverlessly by AWS Bedrock AgentCore. Communication with specialized hardware tools is secured and routed through a dedicated Bedrock AgentCore Gateway to an AWS Lambda target, which dispatches commands directly to physical systems via AWS IoT Core.

`[MARKER - INSERT DIAGRAM: Speech Control Overall Architecture / system_design/img/overall_architecture_topology_aws.png]`

---

## 1. Bidirectional Voice Loops: Bedrock AgentCore & Amazon Nova 2 Sonic

Voice-controlling mechanical joints requires highly responsive, bidirectional audio streaming. Standard HTTP request-response patterns are too slow, introducing multi-second round-trip delays that can cause safety issues in hardware operations.

To resolve this, we leverage the bidirectional WebSocket capabilities of the **Amazon Bedrock AgentCore Runtime** coupled with the **Amazon Nova 2 Sonic** model. Nova Sonic is natively built for low-latency, real-time voice streaming with high-fidelity speech replication.

### 16kHz Audio Synchronization
A frequent issue in voice cockpit development is distorted, high-pitched, or "chipmunk-like" audio playback. This occurs when the browser playback system is misaligned with the model's native sampling rate. 

Amazon Nova Sonic records and streams audio natively at **`16000 Hz` (16kHz)**. To solve audio distortion, we calibrated our custom frontend `AudioPlayer` worklets to match this sample rate exactly:

```javascript
// Calibrating the Audio Context in client-side main.js
const audioContext = new (window.AudioContext || window.webkitAudioContext)({
  sampleRate: 16000 // Force exact alignment with Nova Sonic native 16kHz stream
});
```

This prevents the browser from trying to resample a default `44.1kHz` or `48kHz` stream on-the-fly, which introduces audio artifacts, click sounds, or lag.

### CDK Container-to-Runtime Packaging
With Bedrock AgentCore, the backend container is packaged directly onto the serverless runtime stack using the `@aws-cdk/aws-bedrock-agentcore-alpha` L2 construct library.

The `SpeechControlAgentcoreConstruct` (`cdk/lib/construct/speech-web-agentcore.ts`) builds and uploads the Docker container serverlessly to AWS ECR, automatically filtering out the Python virtualenv and caches to optimize cold-starts:

```typescript
// From cdk/lib/construct/speech-web-agentcore.ts
const agentRuntimeArtifact = agentcore.AgentRuntimeArtifact.fromAsset(
  path.join(__dirname, "../../../speech_control_agentcore"),
  {
    platform: Platform.LINUX_ARM64,
    exclude: [".venv", "__pycache__", "tests"], // Keeps ECR image sizes highly optimized
  }
);
```

When a user initiates a voice session, Bedrock AgentCore dynamically boots an isolated microVM container lane running our FastAPI brain. The voice streams are routed directly through this isolated compute boundary, guaranteeing tenant isolation with near-zero cold-start times.

---

## 2. Zero-Maintenance SigV4 WebSocket Handshaking & Cognito IAM Federation

Authenticating high-velocity WebSocket streams at the cloud boundary usually requires high-cost server proxies (like Nginx, HAProxy, or ECS sidecars) running 24/7. These proxies must parse cookies, manage session states, and sign requests before forwarding them to the AWS API.

To bypass this cost and remove proxy layers completely, we designed a **Zero-Maintenance SigV4 Handshake Pattern** backed by the Cognito Authenticator Stack:

### CDK Cognito Authentication Resources Stack
The CDK project under `cdk/lib/construct/authenticator.ts` provisions a unified security structure containing a Cognito User Pool, Client, and Identity Pool. Users authenticate against the User Pool, and exchange tokens dynamically to pull restricted, temporary credentials:

`[MARKER - INSERT DIAGRAM: Cognito Authenticator Resources Stack / system_design/img/authenticator_resources_aws.png]`

This structure is compiled using CDK constructs as follows:
* **Cognito User Pool**: Manages the operator directory with self-signup disabled to prevent unauthorized account creation.
* **Cognito User Pool Client**: Configured with token validities (ID and Access tokens set to 1 hour, Refresh token set to 30 days).
* **Cognito Identity Pool**: Maps user identity directly to a dedicated AWS IAM role `CognitoDefaultAuthenticatedRole` using federated trust relationships (`sts:AssumeRoleWithWebIdentity`).

### The End-to-End Handshake Flow
Once the federated credentials are vended, the client pre-signs SigV4 WebSocket connections directly inside the browser, establishing an IAM-authenticated path directly to the Bedrock boundary:

`[MARKER - INSERT DIAGRAM: Secure Sign-in and SigV4 Presign Handshake / system_design/img/authenticator_flow_aws.png]`

### The CDK IAM Authorization Binding
To allow frontend clients to establish a WebSocket connection directly with Bedrock, we must bind specific IAM policies to the Cognito Authenticated Role.

In `cdk/lib/cdk-stack.ts`, the authenticated role receives permission to invoke the Bedrock AgentCore Runtime and open the WebSocket stream:

```typescript
// From cdk/lib/cdk-stack.ts
authenticator.authenticatedRole.addToPrincipalPolicy(
  new iam.PolicyStatement({
    effect: iam.Effect.ALLOW,
    actions: [
      "bedrock-agentcore:InvokeAgentRuntime",
      "bedrock-agentcore:InvokeAgentRuntimeWithWebSocketStream",
    ],
    resources: [
      speechControlAgentcoreConstruct.runtimeArn,
      `${speechControlAgentcoreConstruct.runtimeArn}/*`,
    ],
  })
);
```

### Exchanging Federated Credentials via Cognito
1. The operator signs in directly via **AWS Cognito User Pools**.
2. The browser exchanges the resulting JWT ID Token for temporary, restricted AWS credentials from an **AWS Cognito Identity Pool**.
3. Using these temporary credentials, the browser client generates a secure **AWS Signature Version 4 (SigV4)** pre-signed WebSocket URL *directly in JavaScript*:

```javascript
// Generating dynamic AWS SigV4 URL for Bedrock AgentCore Runtime
import { SignatureV4 } from "@aws-sdk/signature-v4";
import { Sha256 } from "@aws-crypto/sha256-js";

async function getPresignedWebSocketUrl(credentials, runtimeArn) {
  const sigv4 = new SignatureV4({
    service: "bedrock-agentcore",
    region: "us-east-1",
    credentials: {
      accessKeyId: credentials.accessKeyId,
      secretAccessKey: credentials.secretAccessKey,
      sessionToken: credentials.sessionToken,
    },
    sha256: Sha256,
  });

  // Generate signed websocket connection URL directly from browser
  const url = await sigv4.presign({
    method: "GET",
    protocol: "wss",
    hostname: "bedrock-agentcore.us-east-1.amazonaws.com",
    path: `/agent-runtime/${runtimeArn}/websocket`,
    headers: { host: "bedrock-agentcore.us-east-1.amazonaws.com" }
  });
  return url;
}
```

This dynamic SigV4 presigned URL allows the browser to connect **directly** to the Bedrock AgentCore Runtime. AWS validates the signature on-the-fly at the network edge, completely eliminating custom gateway middleware and saving thousands of dollars in idle proxy instances!

### Cost-Saving Session Guards
Because serverless container runtime compute costs accumulate while a WebSocket connection remains open, we implemented a strict **30-second token expiration guard** on the frontend:

```javascript
// Check Cognito JWT token validity every 30 seconds
const tokenExpiryGuard = setInterval(() => {
  const jwt = getLocalCognitoToken();
  if (isTokenExpired(jwt)) {
    console.warn("Session expired. Automatically terminating WebSocket to prevent idle AWS charges.");
    clearInterval(tokenExpiryGuard);
    websocket.close(); // Force immediate connection teardown
    triggerHardLogout();
  }
}, 30000);
```

If the Cognito identity token expires, the client immediately drops the connection, ensuring that empty, lingering browser tabs do not consume idle AWS Bedrock AgentCore compute.

### Dynamic Configuration Injection (`config.json`)
To avoid hardcoding references (User Pool ID, Client ID, Identity Pool ID, and Runtime ARN) on the frontend, the CDK stack uses a dynamic injection pattern during bucket deployment:

```typescript
// From cdk/lib/construct/speech-web-agentcore.ts
new s3deploy.BucketDeployment(this, "DeploySpeechWebsiteAndConfig", {
  sources: [
    s3deploy.Source.asset(path.join(__dirname, "../../../speech_control_agentcore/frontend")),
    s3deploy.Source.jsonData("config.json", {
      region: Stack.of(this).region,
      userPoolId: props.userPoolId,
      clientId: props.userPoolClientId,
      identityPoolId: props.identityPoolId,
      runtimeArn: runtime.agentRuntimeArn,
    }),
  ],
  destinationBucket: websiteBucket,
  distribution,
  distributionPaths: ["/*"],
});
```

This generates `config.json` on-the-fly during `cdk deploy` and writes it to the root of our serverless website, ensuring the frontend app remains completely environment-agnostic!

---

## 3. Taming AgentCore Logging: Eliminating Health Check Spam

When deploying a FastAPI application as an AWS Bedrock AgentCore runtime, the Bedrock gateway continually pings the runtime's `/ping` (or `/`) endpoints to perform health checks (typically once every second). 

By default, `uvicorn` (the ASGI server) logs every single one of these access requests at the `INFO` level. Over time, this creates massive log spam in CloudWatch, masking actual application logs and increasing log storage costs:

```text
# Log Spam Example (Without filtering)
INFO:     10.0.12.84:48392 - "GET /ping HTTP/1.1" 200 OK
INFO:     10.0.12.84:48396 - "GET /ping HTTP/1.1" 200 OK
INFO:     10.0.12.84:48400 - "GET /ping HTTP/1.1" 200 OK
```

To resolve this, we implemented a custom Python `logging.Filter` inside `robot_voice_agent.py` to intercept and drop log records generated by `uvicorn.access` if the request path matches the health check endpoints:

```python
# Custom filter to drop access logs for /ping or /
class EndpointFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if record.args and len(record.args) >= 3:
            path = record.args[2]
            if path == "/ping" or path == "/":
                return False # Drop log record
        return True

# Attach the filter to the uvicorn access logger
logging.getLogger("uvicorn.access").addFilter(EndpointFilter())
```

This single filter **saves up to 86,400 log lines per day per active container instance**, ensuring that CloudWatch logs remain readable and log storage costs are minimized.

---

## 4. The Gateway Pattern: Secure Multi-Agent MCP Orchestration

While the **AgentCore Runtime** manages the voice streaming container and user authentication, we cannot allow the container to execute physical joint actions or query physical hardware state directly. Direct access would require the container to hold broad credentials or have direct network access to robot controllers.

Instead, we designed a split architecture:
1. **AgentCore Runtime**: Hosts the voice frontend and FastAPI brain.
2. **AgentCore Gateway (robot-only)**: A secure, isolated micro-gateway exposing a strictly controlled list of robot-only tools using **Model Context Protocol (MCP)**.

### Bedrock AgentCore L2 Sandbox Targets
The CDK project under `cdk/lib/construct/robot-tool-gateway.ts` defines a strict dual-target sandbox. Under this model, physical robot controls (`robot-only-mcp-lambda`) and digital presenter text-to-speech systems (`digital-human-mcp-lambda`) execute in separate isolated lanes:

`[MARKER - INSERT DIAGRAM: AWS Bedrock AgentCore L2 Sandbox Targets / system_design/img/robot_tool_gateway_sandbox_aws.png]`

### Gateway Authorization & Execution Flow
External edge devices utilize the dedicated `SkillMcpUser` credentials to query the gateway securely, isolating backend workloads from broad execution scopes:

`[MARKER - INSERT DIAGRAM: AWS Bedrock AgentCore Secure Gateway Execution Flow / system_design/img/robot_tool_gateway_flow_aws.png]`

### Secure, Signed SSE Transports with `httpx` and `SigV4`
Because the Bedrock Gateway has `usingAwsIam()` authorization configured, the FastAPI speech container cannot query tools anonymously. We developed a custom `AwsSigV4Auth` transport hook using `httpx` to sign all Server-Sent Events (SSE) requests with AWS SigV4:

```python
# From speech_control_agentcore/backend/tools/mcp_client.py
from botocore.auth import SigV4Auth as BotocoreSigV4Auth
from botocore.awsrequest import AWSRequest
import httpx

class AwsSigV4Auth(httpx.Auth):
    requires_request_body = True

    def auth_flow(self, request: httpx.Request):
        # Resolve short-lived IAM credentials from local environment
        credentials = _resolve_frozen_credentials()
        aws_region = _resolve_region()
        
        # Strip headers that violate signing constraints
        headers = dict(request.headers)
        headers.pop("connection", None)

        aws_request = AWSRequest(
            method=request.method,
            url=str(request.url),
            data=request.content,
            headers=headers,
        )
        # Sign requests targeting 'bedrock-agentcore' service name
        BotocoreSigV4Auth(credentials, "bedrock-agentcore", aws_region).add_auth(aws_request)

        # Apply signed headers back to outgoing HTTP request
        for header_name, header_value in dict(aws_request.headers).items():
            request.headers[header_name] = header_value

        yield request
```

This `AwsSigV4Auth` hook is registered directly in our `httpx.AsyncClient` wrapper, letting our Strands `MCPClient` securely list and call tools:

```python
async with httpx.AsyncClient(auth=AwsSigV4Auth()) as client:
    async with streamable_http_client(self.server_url, http_client=client) as streams:
        yield streams
```

### Low-Latency Process Warmup Sequence
To prevent a cold-start latency spike on the first spoken query, we configured the FastAPI container lifecycle (`@asynccontextmanager`) to warmup and cache the tool schemas in the container's RAM at boot time:

```python
# From speech_control_agentcore/backend/robot_voice_agent.py
@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("🤖 Robot Voice Control AgentCore Service starting up...")
    try:
        warmed_tools = warmup_tools()
        logger.info(f"MCP tools warmed at startup: {len(warmed_tools)} loaded")
    except Exception as e:
        logger.warning(f"MCP tool warmup failed at startup: {e}")
    yield
    cleanup_tools()
```

By warming and caching MCP tool schemas during the container boot cycle, first-turn spoken query latency is slashed, ensuring near-instantaneous command processing.

### Environment-Driven Application Firewall
To prevent the model from executing unauthorized tools, the CDK stack defines strict container-level environmental constraints:

```typescript
// From cdk/lib/construct/speech-web-agentcore.ts
environmentVariables: {
  MCP_TOOL_PREFIX_ALLOW: "robot-only-mcp-lambda___robot_",
  MCP_TOOL_NAME_ALLOW: SUPPORTED_ROBOT_GATEWAY_TOOL_NAMES,
}
```

The python backend enforces these configurations during discovery:

```python
# From speech_control_agentcore/backend/tools/robot_actions.py
_ALLOWED_PREFIXES = tuple(p.strip() for p in os.environ.get("MCP_TOOL_PREFIX_ALLOW", "").split(",") if p.strip())
_ALLOWED_NAMES = {n.strip() for n in os.environ.get("MCP_TOOL_NAME_ALLOW", "").split(",") if n.strip()}

def _matches_allowed_prefix(tool: Any) -> bool:
    return _tool_name(tool).startswith(_ALLOWED_PREFIXES)

def _matches_allowed_name(tool: Any) -> bool:
    return _tool_name(tool) in _ALLOWED_NAMES
```

This environment mapping forms a secure, serverless application firewall that restricts execution strictly to the defined robotics command catalog.

---

## 5. Exact Naming & Lambda Tool-Name Extraction Contracts

Integrating the MCP gateway with AWS Lambda targets introduces a major challenge: **name mismatch errors** during tool calls.

By default, Bedrock AgentCore exposes tools from Lambda targets with a specific prefix:
- Gateway Target Name: `robot-only-mcp-lambda`
- Tool Name: `robot_wave`
- Exposed Name to MCP Client: `robot-only-mcp-lambda___robot_wave`

Trying to normalize or strip these prefixes on the container client side introduces risk and leads to the gateway throwing a validation error:
`Gateway request is missing a supported tool name. candidate_locations=[]`

To achieve high reliability, we established two strict architectural contracts:

### Client Naming Contract
The speech runtime uses the **exact AgentCore gateway-visible tool names** end-to-end. It does not rename them before passing them to the model, and calls `tools/call` with the raw prefixed name:

```json
{
  "method": "tools/call",
  "params": {
    "name": "robot-only-mcp-lambda___robot_wave",
    "arguments": { "robot_ids": ["robot_1"] }
  }
}
```

### Direct Gateway Target Execution: Eliminating Public Lambda URLs
Once the gateway maps and forwards the request, the Lambda target executes downstream tasks including DynamoDB caching, Polly synthesis, and IoT Core topic publishing.

Unlike the text control plane, which may utilize a dual-authorized Lambda Function URL for direct external API connections, the **Speech Control Cockpit enforces a zero-public-ingress architecture**. 

There are **no Lambda Function URLs** deployed for the speech control tool execution targets. 

Instead, the Bedrock AgentCore Secure Gateway invokes the target Lambda functions (`RobotToolFunction` and `DigitalHumanToolFunction`) directly using the AWS SDK integration. This completely removes public HTTP endpoints from the tool-execution layer:

1. **Zero External Exposure**: The tool execution Lambda has no public endpoints or Function URLs, ensuring that malicious actors cannot scan, probe, or DDOS the robotics actuator logic.
2. **Gateway-Mediated Invocation**: All traffic must pass through the Bedrock AgentCore Gateway, which validates IAM SigV4 signatures at the AWS cloud frontier before forwarding requests.
3. **Decoupled Downstream Execution**: Once validated and dispatched by the gateway, the Lambda target executes downstream tasks—publishing to AWS IoT Core MQTT topics, caching speech syntheses in DynamoDB, and uploading Polly audio streams to S3—while remaining entirely shielded from the public internet.

### Lambda Tool-Name Extraction Contract
Inside the target Lambda handler (`mcp_server/robot_tool_lambda.py`), we extract the tool name by following the documented AgentCore context contract, and strip the prefix before internal dispatch:

```python
# Extracting tool name securely in AWS Lambda
def _extract_tool_name(context: Any, event: Any) -> str:
    # 1. Look in client context custom fields (Highest priority)
    client_context = getattr(context, "client_context", None)
    custom = getattr(client_context, "custom", None)
    tool_name = getattr(custom, "bedrockAgentCoreToolName", None)
    
    # 2. Fallback to direct context property
    if not tool_name:
        tool_name = getattr(context, "bedrockAgentCoreToolName", None)
        
    if not tool_name:
        raise ValueError("Gateway request is missing a supported tool name.")
        
    # Strip target prefix: 'robot-only-mcp-lambda___robot_wave' -> 'robot_wave'
    if "___" in tool_name:
        return tool_name.split("___", 1)[1]
        
    return tool_name
```

By adhering to this exact context-extraction pattern, the Lambda target resolves tool calls flawlessly without parsing raw HTTP bodies, solving the gateway routing exceptions and bringing joint execution latencies down to milliseconds!

---

## 6. Bringing Agents to Life: Dual Live2D Avatar Lip-Syncing

To offer an immersive operator experience, the cockpit dashboard renders two live-animated **Live2D avatars** representing the user (on the left) and the AI assistant (on the right). These avatars must react and animate their mouths dynamically in sync with real-time vocal audio inputs and playbacks.

### Real-Time Audio RMS Extraction
The lip-sync animation engine relies on continuous Root Mean Square (RMS) calculation to extract the current volume (amplitude) of the voice streams:

1. **Assistant Speech**: Calculated in real-time inside the Web Audio API's `AudioWorklet` processor during streaming playback. The `AudioPlayer` flushes the RMS data to the main animation loop.
2. **User Speech**: Tracked by computing the RMS of the microphone's input stream directly inside the client-side `main.js`.

### The Cubism 2 Parameter-Writing Contract
The rendering layer utilizes the Live2D Cubism 2 SDK. A key challenge is that different third-party avatar models use different internal naming conventions for the mouth-open parameter. If the code only tries to write to a single parameter ID, many models will fail to lip-sync, remaining statically shut.

To prevent this regression and support all standard models, the WebGL rendering engine (`public/live2d-avatar.js`) must write the calculated RMS mouth-open value (scaled between `0.0` and `1.0`) across **all standard Cubism 2-compatible parameter IDs** sequentially within each animation frame loop:

```javascript
// Iterating and writing parameters to the Live2D model instance
const mouthValue = currentRMS * volumeMultiplier; // Normalized 0.0 - 1.0

// Try multiple compatible parameter IDs to support different model conventions
const parameterIDs = [
  "ParamMouthOpenY",
  "PARAM_MOUTH_OPEN_Y",
  "ParamMouthOpen",
  "PARAM_MOUTH_OPEN",
  "ParamA"
];

parameterIDs.forEach(id => {
  try {
    model.setParameterValue(id, mouthValue);
  } catch (err) {
    // Gracefully handle model instances that lack specific parameter keys
  }
});
```

### Essential Gotchas & Cache Busting
- **Immediate Returns Regression**: An earlier implementation attempted to return early after the first successful parameter write. However, some advanced models require writing to *both* `ParamMouthOpen` and `ParamMouthOpenY` concurrently to trigger complex mesh deformations. Eliminating the early-return ensures both parameters update, restoring smooth, natural lip-syncing across all models.
- **Aggressive Browser Cache-Busting**: During cloud deployments, web browsers aggressively cache localized JavaScript canvas modules. To ensure that the updated rendering logic is loaded instantly by operators without requiring manual hard-reloads, we append dynamic query string version parameters inside the HTML entrypoint:

```html
<!-- Forcing script re-evaluation using cache-busting version numbers -->
<script src="js/live2d-avatar.js?v=1.0.4" type="module"></script>
<script src="js/main.js?v=1.0.4" type="module"></script>
```

---

## Conclusion: Voice-Activated Robotics is Here

By coupling the low-latency voice capabilities of **Amazon Nova 2 Sonic** with the serverless scaling of **Amazon Bedrock AgentCore**, we have built a highly secure, cost-effective, and robust cockpit to orchestrate humanoid fleets and autonomous quadcopters.

By pre-signing SigV4 connections in the browser, implementing FastAPI health check filters to clean CloudWatch log spam, enforcing exact naming contracts across MCP gateways, and utilizing dual Live2D lip-syncing, we have created an enterprise-ready architecture that is both highly resilient and zero-maintenance.

The entire system is modular, fully serverless, and optimized for immediate deployment. Get started today by deploying the CDK stack and commanding your own fleet of intelligent embodied agents!

---

### Have questions?
Let us know in the comments below, or check out our architectural guide inside the project repository!
