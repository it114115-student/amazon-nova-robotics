# Security and Logic Updates - June 2026

## 1. Security Hardening (AWS Infrastructure)
To protect against unauthorized resource consumption (AWS Bedrock & AWS Polly), the following security measures have been implemented:

### REST API Authorization
- **Endpoints Secured**: `/api/live-status` and `/api/battle-result`.
- **Mechanism**: Switched from `AuthorizationType.NONE` to `AuthorizationType.COGNITO`.
- **Implementation**: The API Gateway now validates the Cognito ID Token passed in the `Authorization` header before allowing the request to reach the Lambda backend.
- **Reference**: [domain-expansion-serverless.ts](../cdk/lib/construct/domain-expansion-serverless.ts)

### WebSocket Security
- **Mechanism**: Custom Lambda Authorizer for connection establishment.
- **Validation**: Manually verifies the JWT signature, issuer, and expiry using the Cognito Public JWKS (JSON Web Key Set).
- **Reference**: [auth.py](../domain-expansion-ar-game-serverless/backend/auth.py)

### Cost-Saving Session Guards
- **Mechanism**: Client-side `setInterval` polling (every 30 seconds).
- **Implementation**: The frontend (`auth.js`, `auth-check.js`, `index.html`) locally decodes the Cognito JWT to inspect the `exp` claim. If expired, it triggers an immediate local logout sequence which specifically forces `.close()` on all active WebSockets.
- **Benefit**: Ensures dormant browsers do not hold expensive serverless WebSocket connections (like AgentCore runtimes) open infinitely after authentication expires, resulting in zero compute cost for the idle guard checks.

---

## 2. AWS Polly Audio Playback Logic
The audio logic is optimized for low-latency streaming and high synchronization.

### "Stop & Crop" Logic
- **Immediate Interruption**: When a new commentary event is triggered, `stopCurrentCommentaryAudio()` is called. This clears the `src`, flushes the buffer, and detaches event listeners to prevent legacy playback from interfering with new audio.
- **Safety Timeout**: A hardware-level fallback is implemented at `effectiveDuration + 5000ms`. If the `onended` event fails to fire (due to streaming stalls), the system forces a state resolution to keep the game moving.
- **Mute Synchronization**: When volume is 0%, the system skips playback but maintains a calculated delay based on text length to keep the match timeline synchronized with audible viewers.

---

## 3. Player View & Dual Monitor Logic
Enhanced support for secondary displays (Popup Player Window).

### Video Playback Modes
- **Integrated Mode**: Videos play directly over the AR camera view. In "Battle Role" mode, this is hidden to prevent obstructing the hand tracking visuals.
- **Popup Mode (Dual Monitor)**: Videos play in an external tab. This is now enabled for all states:
    - **Sandbox**: Normal playback.
    - **Standby**: Gestures recognized while waiting in a room now trigger videos on the popup screen.
    - **Active Match**: Domain/Technique videos are sent via `postMessage` to the external window.
    - **Match Results**: Win/Lose cinematics are now forwarded to the popup window.

### Standby Synchronization
- Gestures performed during the "Standby" phase (before match start) are now broadcast to the room. This allows the audience and opponent to see "warm-up" actions.

---

## 4. Local vs. AWS Compatibility
- **Local Mode**: The system remains fully compatible with local `OpenClaw` server modes. 
- **Media Assets**: Asset path resolution in `getVideoUrl()` dynamically switches between `localhost` and GitHub Pages depending on the environment.
- **Authentication**: When running locally without AWS credentials, the system supports a "No-Auth" fallback or bridge-based forwarding to development clusters.

---

## 5. Server-Side Technique Triggering & Orchestration (`/api/trigger-technique`)
To centralize and optimize robot control and audio synthesis, the game orchestrates JJK techniques via the serverless backend instead of sending direct, raw commands from the client browser.

### Architectural Workflow:
1. **Client Trigger:** When a player performs a hand sign gesture, the game client sends a single `POST` request to the secure backend endpoint `/api/trigger-technique` with the payload:
   ```json
   {
     "technique": "hollow_purple",
     "robotId": "all",
     "role": "player1"
   }
   ```
2. **Server-Side Mapping (`JJK_ACTION_MAP`):** The serverless Lambda backend maintains the canonical translation map mapping JJK moves to physical simulator stances and Japanese Polly speech text:
   - **`lapse_blue`** ➔ Stance: `left_shot_fast`, Speech: `"術式順転、蒼"`
   - **`reversal_red`** ➔ Stance: `right_shot_fast`, Speech: `"術式反転、赫"`
   - **`hollow_purple`** ➔ Stance: `kick`, Speech: `"虚式、茈"`
3. **Concurrent Execution:** The serverless backend triggers the physical action and the AWS Polly voice concurrently:
   - **Physical Action:** Makes a direct REST POST call to the configured `ROBOT_API_ENDPOINT` (`/run_action/{target}`).
   - **Speech Synthesis:** Invokes the Robotics MCP Lambda server asynchronously (`robot_speak` tool) to synthesize Polly audio without blocking the physical motion execution.

### Backwards-Compatible Local Fallback:
If the serverless backend is unavailable (or the game is running in static local mode), the client browser automatically catches the failure and falls back to direct client-side direct calling:
- Directly triggers `/run_action/{robot_id}` on the local robot simulator endpoint configured in the Settings Panel, guaranteeing offline/local compatibility and preserving existing hardware integration workflows.


---

## 6. Multi-Modal Snapshots & Configurable Session Expiration (June 14, 2026)

### A. Robust OpenClaw Gateway XML Snapshot Bypass
- **Problem**: When playing matches behind the intermediate OpenClaw proxy gateway, custom payload root attributes (e.g., `"image"`, `"image_p2"`) were stripped, and multimodal nested block arrays inside `"messages"` were flattened into single plain-text prompt strings. This dropped the player webcam snapshots entirely, preventing the Kugisaki Nobara AI commentator from trash-talking or hyping player appearances.
- **Solution**: 
  - **Sender packaging (`commentary.py`)**: Before dispatching payloads to the agent runtime, the backend Lambda embeds the base64-encoded JPEGs inside structured plain-text tags (`<p1_webcam_base64_jpeg>...</p1_webcam_base64_jpeg>` and `<p2_webcam_base64_jpeg>...</p2_webcam_base64_jpeg>`) appended directly to the text of the prompt.
  - **Receiver extraction (`commentator_agent.py`)**: Inside our custom container-backed agent, a regex-based parser extracts and decodes the base64 image strings from the XML tags, converts them back to Bedrock binary multimodal parts, and completely strips the XML tags from the final text prompt.
  - **Benefit**: Retains 100% token efficiency and ensures webcam image context survives any proxy gateway flattening, while preserving normal direct/local JSON file-based snapshot operations when no tags are present.

### B. Technique/Domain Translation Tracker Keys mapping
- **Problem**: Raw gesture outputs from the hand-tracker model (e.g., `"Authentic Mutual Love"` and `"Yuji Itadori"`) did not perfectly align with regional translation dictionary keys inside `battle.js`, causing the player's active HUD and generated commentary details to default to English even when Cantonese (`zh-HK`), Taiwanese (`zh-TW`), or Japanese (`ja`) were selected.
- **Solution**: Updated `TECHNIQUE_TRANSLATIONS` to add direct tracker alias keys (`"Authentic Mutual Love"` and `"Yuji Itadori"`) mapping to their correct localized versions for all languages. They now display perfectly in Chinese characters and are sent to the AI commentator correctly localized (e.g. `真贋相愛` or `虎杖悠仁的領域`).

### C. Configurable Cognito Session Token Expirations
- **Session Durations**: Explicitly set `idTokenValidity` and `accessTokenValidity` to **1 hour** by default on the User Pool Client to match security expectations, with `refreshTokenValidity` defaulting to **30 days**.
- **CDK Configuration**: Implemented parameter support both programmatically via `AuthenticatorProps` and dynamically via command-line context variables (`idTokenValidityHours`, `accessTokenValidityHours`, `refreshTokenValidityDays`). This allows operators to easily adjust session policies during deployments without modifying stack codebase files.


---

## 7. Architecture Refactoring & MCP Server Streamlining (June 13-14, 2026)

To streamline resources and optimize our serverless footprint, a major architectural refactoring of the Model Context Protocol (MCP) server integration, storage buckets, and text processing pipelines has been completed:

### A. Streamlined CDK Architecture & De-Cluttering
- **MCP Server Consolidation**: Removed the legacy, dedicated `LambdaMcpServerConstruct` (`cdk/lib/construct/mcp-server.ts` and `mcp_server/index.py`) in favor of direct tool integrations, reducing cold start latencies and AWS Lambda compute bloat.
- **Direct Database Coupling**: Modified the `TextControlWebConstruct` to bypass the intermediate MCP server stack and reference the DynamoDB `speechTable` directly.
- **Unified Media Storage**: Refactored the `RobotToolGatewayConstruct` and corresponding backend endpoints to use a centralized `mediaBucket` (under environment variable `MEDIA_BUCKET_NAME`) instead of the separate, isolated `imageBucket`. This simplifies permission models and asset lifecycles.

### B. Intelligent TTS Markdown Sanitization
- **Issue**: Standard AI-generated commentaries frequently contain markdown syntax (e.g. `**bold text**`, headings `#`, or bullets `-`), which raw Text-to-Speech (Polly) services would try to pronounce literally, resulting in robotic and jarring audio.
- **Solution**: Enhanced `commentary_tts.py` to parse text through a BeautifulSoup HTML extractor and a Markdown compiler to strip all markdown tags and format symbols before sending text to AWS Polly, ensuring clean and human-sounding voice delivery.
- **Dependencies**: Added `markdown` and `beautifulsoup4` packages to the Lambda `requirements.txt`.

### C. Standardized Gateways & Real-Time Monitoring
- **Centralized Tool Invocation**: Introduced a standardized helper function `invoke_agentcore_gateway_tool` in `lambda_function.py` for routing tool execution seamlessly through the AgentCore Gateway.
- **Robot Camera Viewer**: Deployed a dedicated web portal (`robot-media-website/index.html`) specifically tailored for real-time monitoring and streaming of physical/simulated robot camera viewfeeds.
- **Offline Gateway Testing**: Added a local developer test script (`scratch/test_mcp.py`) to verify tool routing and API Gateway compatibility before deployment.


---

## 8. Secure Xiaoice Credentials & Project-Specific API Key Management (June 13, 2026)

To secure multi-project Xiaoice conversational AI deployments and prevent exposure of critical upstream partner developer keys, a complete credentials isolation and verification system was implemented:

### A. AWS Secrets Manager Key Vault
- **Construct Isolation**: Configured `TextControlWebConstruct` to provision an AWS Secrets Manager secret (`XiaoiceProjectCredentials`) containing the access key and secret key mappings for various active projects.
- **Client Metadata Seeding**: Reads local developer credentials (`text_control/xiaoice_credentials.json`) during CDK synth to seed the initial cloud secret values.
- **Granular IAM Policies**: Granted strict read-only permissions (`grantRead`) to the Lambda Flask backend, keeping the master database credentials hidden from all other client roles.

### B. Project-Specific HMAC V2 Signatures
- **HMAC Signatures Calculation (`auth.py`)**: Rebuilt the request signature verification engine to implement a rigorous sorting and hashing method:
  1. Build a key-value parameter map: `{"bodyString": body_data, "secretKey": secret_key, "timestamp": timestamp_header}`.
  2. Sort parameters alphabetically by key name in ascending order, then concatenate into an ampersand-delimited query string (`bodyString=...&secretKey=...&timestamp=...`).
  3. Hash the resulting string using `SHA-512` and convert it into an uppercase hexadecimal string.
- **Zero-Trust Validation**: When an incoming webhook/API request is received, the backend queries the database mapping using the provided `X-Key` header. If a matching secret key is found, it evaluates the calculated signature against the `X-Sign` header, rejecting unauthorized requests before they consume compute/TTS resources.

### C. Deterministic Key Generator Tool
- **Utility Script (`generate_keys.py`)**: Introduced an automated command-line tool for developers to generate new project-specific credentials safely.
- **Flexible Modes**: Supports both standard high-entropy random key generation (`secrets.token_hex`) and seed-based deterministic HMAC-SHA256 generation. This guarantees that developers can reproduce key pairs deterministically across multi-region offline clusters using a master seed.


---

## 9. Comprehensive Git Commit History Log (June 13 - June 14, 2026)

This log catalogues all Git commits made over the last 24 hours, tracking the progression from credential management to architectural streamlining, image-handling optimizations, and dynamic session parameters.

### Commit 1: `3b536b1` (June 13, 2026)
- **Author**: Cyrus <cywong@vtc.edu.hk>
- **Subject**: `feat: implement Xiaoice credentials management with AWS Secrets Manager; add key generation tool and update API authentication to support project-specific keys`
- **Impact & Architectural Context**:
  - Implemented the master `XiaoiceProjectCredentials` CDK secrets mapping and Flask-based authentication verification.
  - Added [generate_keys.py](../text_control/generate_keys.py) to manage dynamic access control credentials.
  - Added documentation files [speech_control_agentcore/README.md](../speech_control_agentcore/README.md) and [text_control/README.md](../text_control/README.md).

### Commit 2: `480fb2d` (June 14, 2026)
- **Author**: Cyrus <cywong@vtc.edu.hk>
- **Subject**: `Refactor MCP Server and related constructs to improve media handling and integrate markdown processing`
- **Impact & Architectural Context**:
  - Decoupled the old MCP Server architecture by completely removing [mcp-server.ts](../cdk/lib/construct/mcp-server.ts) and [mcp_server/index.py](../mcp_server/index.py) to reduce compute overhead and cold starts.
  - Unified file upload lifecycles into a single `MEDIA_BUCKET_NAME` storage.
  - Added BeautifulSoup and Markdown filtering to [commentary_tts.py](../domain-expansion-ar-game-serverless/backend/commentary_tts.py) to strip formatting notation from synthesizers.
  - Deployed the real-time robot video monitoring web portal [robot-media-website/index.html](../robot-media-website/index.html).

### Commit 3: `2557aa1` (June 14, 2026)
- **Author**: Cyrus <cywong@vtc.edu.hk>
- **Subject**: `feat: enhance image handling and XML tag extraction in commentary and lambda functions; update requirements for langdetect`
- **Impact & Architectural Context**:
  - Resolved OpenClaw proxy stripping limitations by developing an XML-based prompt payload packaging scheme (`<p1_webcam_base64_jpeg>` and `<p2_webcam_base64_jpeg>`) in [commentary.py](../domain-expansion-ar-game-serverless/backend/commentary.py).
  - Programmed regex-based parsing and extraction of the inline XML image bodies inside [commentator_agent.py](../domain-expansion-commentator-agentcore/commentator_agent.py), converting them to multimodal parts and feeding them cleanly into Bedrock.
  - Localized character techniques and domain expansions for active game screens and comments.

### Commit 4: `b98d3f3` (June 14, 2026)
- **Author**: Cyrus <cywong@vtc.edu.hk>
- **Subject**: `feat: add configurable session expiration for Cognito tokens; update AuthenticatorProps to support dynamic token lifetimes`
- **Impact & Architectural Context**:
  - Configured Cognito access and identity tokens to enforce standard **1-hour** expirations by default.
  - Refactored [authenticator.ts](../cdk/lib/construct/authenticator.ts) to accept deployment-time context variables (`idTokenValidityHours`, `accessTokenValidityHours`, `refreshTokenValidityDays`) to make expirations configurable without altering stack source code.
