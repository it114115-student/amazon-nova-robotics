# Security and Logic Updates - June 2026

## 1. Security Hardening (AWS Infrastructure)
To protect against unauthorized resource consumption (AWS Bedrock & AWS Polly), the following security measures have been implemented:

### REST API Authorization
- **Endpoints Secured**: `/api/live-status` and `/api/battle-result`.
- **Mechanism**: Switched from `AuthorizationType.NONE` to `AuthorizationType.COGNITO`.
- **Implementation**: The API Gateway now validates the Cognito ID Token passed in the `Authorization` header before allowing the request to reach the Lambda backend.
- **Reference**: [domain-expansion-serverless.ts](../cdk/lib/construct/domain-expansion-serverless.ts)

### WebSocket Security
- **Mechanism**: Custom Lambda Authorizer.
- **Validation**: Manually verifies the JWT signature, issuer, and expiry using the Cognito Public JWKS (JSON Web Key Set).
- **Reference**: [auth.py](../domain-expansion-ar-game-serverless/backend/auth.py)

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
