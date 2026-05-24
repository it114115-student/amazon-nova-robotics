import os
import json
import logging
import time
import base64
import re

# Configure Logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Global Placeholders for Lazy Loading
boto3 = None
Key = None
dynamodb = None
connections_table = None
sessions_table = None

connections_table_name = os.environ.get("CONNECTIONS_TABLE", "DomainExpansionConnections")
sessions_table_name = os.environ.get("SESSIONS_TABLE", "DomainExpansionSessions")

# Agent Configuration Defaults
DEFAULT_AGENT_TYPE = os.environ.get("AGENT_TYPE", "agentcore_runtime") # 'openclaw' | 'strands_local' | 'agentcore_runtime'
OPENCLAW_GATEWAY_URL = os.environ.get("OPENCLAW_GATEWAY_URL", "http://127.0.0.1:18789")
OPENCLAW_TOKEN = os.environ.get("OPENCLAW_TOKEN", "")
OPENCLAW_AGENT_ID = os.environ.get("OPENCLAW_AGENT_ID", "domain-commentator")
BEDROCK_MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "amazon.nova-pro-v1:0")
BEDROCK_REGION = os.environ.get("BEDROCK_REGION", "us-east-1")
AGENTCORE_RUNTIME_ARN = os.environ.get("AGENTCORE_RUNTIME_ARN", "")

# JJK Character Translations (Translate base English name tokens to JJK lore terms)
def translate_detail(text: str) -> str:
    if not text:
        return text
    # Standard replacement maps
    replacements = {
        r"\brobot_1\b": "Fushiguro Megumi (Robot 1)",
        r"\brobot_2\b": "Kugisaki Nobara (Robot 2)",
        r"\brobot_3\b": "Itadori Yuji (Robot 3)",
        r"\brobot_4\b": "Inumaki Toge (Robot 4)",
        r"\brobot_5\b": "Ryomen Sukuna (Robot 5)",
        r"\brobot_6\b": "Gojo Satoru (Robot 6)",
        r"\bdrone_1\b": "Ushiushi Great Curse (Drone 1)",
        r"\bdrone_2\b": "Nue Storm-summoner (Drone 2)",
        r"\bdog_1\b": "Divine Dog: White (Dog 1)",
        r"\bdog_2\b": "Divine Dog: Black (Dog 2)",
        r"\bdog_3\b": "Divine Dog: Totality (Dog 3)",
        r"\bxiaoice_1\b": "Zen'in Maki (Xiaoice)",
        r"\bdogMoveForward\b": "releases Divine Dog to charge forward",
        r"\bdogMoveBackward\b": "recalled Divine Dog moving back",
        r"\bdogTurnLeft\b": "ordered Divine Dog left maneuver",
        r"\bdogTurnRight\b": "ordered Divine Dog right maneuver",
        r"\bdroneTakeoff\b": "summons Nue flight takeoff",
        r"\bdroneLand\b": "recalled Nue landing down",
        r"\bdroneMoveForward\b": "guided Nue gliding forward",
        r"\bdroneMoveBackward\b": "guided Nue gliding back",
        r"\bdroneTurnLeft\b": "steered Nue turning left",
        r"\bdroneTurnRight\b": "steered Nue turning right",
        r"\brobotMoveForward\b": "pushes sorcerer dash forward",
        r"\brobotMoveBackward\b": "slides sorcerer retreat back",
        r"\brobotTurnLeft\b": "steered sorcerer left pivot",
        r"\brobotTurnRight\b": "steered sorcerer right pivot",
        r"\brobotGesture1\b": "activated Divergent Fist technique",
        r"\brobotGesture2\b": "activated Black Flash release",
        r"\brobotGesture3\b": "activated Domain Expansion invocation",
        r"\brobotGesture4\b": "activated Cursed Speech commands",
        r"\bxiaoiceGesture1\b": "invokes Maki's Special Grade tool swing",
        r"\bxiaoiceGesture2\b": "invokes Maki's high-speed intercept",
        r"\bxiaoiceGesture3\b": "invokes Maki's Cursed Energy discharge",
    }
    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text

# Fetch Character Instructions for Strands Local Engine
def load_system_prompt() -> str:
    # Attempt to load IDENTITY.md and SOUL.md if present
    # In Lambda environment, these are packaged or can be set as fallbacks
    identity = ""
    soul = ""
    try:
        if os.path.exists("IDENTITY.md"):
            with open("IDENTITY.md", "r", encoding="utf-8") as f:
                identity = f.read()
        if os.path.exists("SOUL.md"):
            with open("SOUL.md", "r", encoding="utf-8") as f:
                soul = f.read()
    except Exception as e:
        logger.warning(f"Could not read prompt markdown files: {e}")

    if not identity:
        identity = """# Character Identity: Kugisaki Nobara (钉崎野蔷薇)
- Role: High-energy JJK match commentator.
- Personality: Feisty, extremely confident, slightly arrogant, styling, fashion-loving, and deeply competitive.
- Language: High-octane, sassy, blending English & Chinese naturally. Use JJK terms (Domain Expansion, cursed techniques, Black Flash).
- Tone: Dynamic, energetic, hyping up technique executions! Keep each output to 2-3 short, punchy sentences max!"""

    if not soul:
        soul = """# Commentary Guidelines
- Deliver commentary directly to the player, trash-talking their mistakes or screaming with excitement at a high score.
- Incorporate specific sorcerer profiles like Fushiguro Megumi, Gojo Satoru, or Nue Cursed birds depending on commands.
- Never use robotic placeholders, speak with absolute passion and raw sorcerer attitude."""

    return f"{identity}\n\n{soul}"


# Main Router
def lambda_handler(event, context):
    global boto3, Key, dynamodb, connections_table, sessions_table
    if boto3 is None:
        import boto3 as _boto3
        from boto3.dynamodb.conditions import Key as _Key
        boto3 = _boto3
        Key = _Key
        dynamodb = boto3.resource("dynamodb")
        connections_table = dynamodb.Table(connections_table_name)
        sessions_table = dynamodb.Table(sessions_table_name)

    logger.info(f"Incoming Event: {json.dumps(event)}")
    
    # 1. Detect WebSocket API Gateway connection
    request_context = event.get("requestContext", {})
    if "connectionId" in request_context:
        return handle_websocket(event, request_context)
        
    # 2. Treat as HTTP API Gateway REST call
    return handle_http(event)


# WebSocket API Handler
def handle_websocket(event, r_ctx):
    connection_id = r_ctx.get("connectionId")
    route_key = r_ctx.get("routeKey")
    logger.info(f"WebSocket Connection ID: {connection_id}, Route Key: {route_key}")

    # Initialize API Gateway Management client to send messages back
    domain = r_ctx.get("domainName")
    stage = r_ctx.get("stage")
    ws_endpoint = f"https://{domain}/{stage}"
    apigw_client = boto3.client("apigatewaymanagementapi", endpoint_url=ws_endpoint)

    def post_to_conn(target_conn_id, data):
        try:
            apigw_client.post_to_connection(
                ConnectionId=target_conn_id,
                Data=json.dumps(data)
            )
        except Exception as e:
            logger.warning(f"Could not post to connection {target_conn_id}: {e}")

    def query_room_connections(room_code):
        try:
            # Query index RoomCodeIndex
            response = connections_table.query(
                IndexName="RoomCodeIndex",
                KeyConditionExpression=Key("room_code").eq(room_code)
            )
            return response.get("Items", [])
        except Exception as e:
            logger.error(f"Error querying room connections: {e}")
            return []

    if route_key == "$connect":
        logger.info(f"Client connected: {connection_id}")
        return {"statusCode": 200, "body": "Connected."}

    elif route_key == "$disconnect":
        logger.info(f"Client disconnected: {connection_id}")
        # Look up room code before deletion
        try:
            record_resp = connections_table.get_item(Key={"connection_id": connection_id})
            record = record_resp.get("Item")
            if record:
                room_code = record.get("room_code")
                client_id = record.get("client_id")
                role = record.get("role")
                
                # Delete connection
                connections_table.delete_item(Key={"connection_id": connection_id})
                
                # Broadcast departure
                room_conns = query_room_connections(room_code)
                for conn in room_conns:
                    target_id = conn.get("connection_id")
                    if target_id != connection_id:
                        post_to_conn(target_id, {
                            "type": "user_left",
                            "data": {
                                "id": client_id,
                                "role": role
                            }
                        })
        except Exception as e:
            logger.error(f"Error during disconnect cleanup: {e}")
        return {"statusCode": 200, "body": "Disconnected."}

    # Custom WebSocket action handler
    try:
        body = json.loads(event.get("body", "{}"))
        action = body.get("action")
        logger.info(f"WebSocket custom action parsed: {action}")

        if action == "join_room":
            room_code = body.get("roomCode", "BTL1")
            role = body.get("role", "viewer")
            client_id = body.get("client_id", "anonymous")

            # Save connection mapping
            connections_table.put_item(
                Item={
                    "connection_id": connection_id,
                    "client_id": client_id,
                    "room_code": room_code,
                    "role": role,
                    "created_at": int(time.time())
                }
            )
            logger.info(f"Saved connection mapping: {connection_id} -> Room: {room_code}, Role: {role}")

            # Notify all other room participants
            room_conns = query_room_connections(room_code)
            for conn in room_conns:
                target_id = conn.get("connection_id")
                if target_id != connection_id:
                    post_to_conn(target_id, {
                        "type": "user_joined",
                        "data": {
                            "id": client_id,
                            "role": role
                        }
                    })

        elif action == "signal":
            sig_type = body.get("type")
            sig_data = body.get("data")
            to_client = body.get("to")

            # Find sender's parameters
            sender_resp = connections_table.get_item(Key={"connection_id": connection_id})
            sender = sender_resp.get("Item")
            if not sender:
                logger.warning(f"Sender connection mapping missing: {connection_id}")
                return {"statusCode": 404, "body": "Sender missing"}

            sender_id = sender.get("client_id")
            sender_role = sender.get("role")
            room_code = sender.get("room_code")

            payload = {
                "type": "signal",
                "data": {
                    "from": sender_id,
                    "role": sender_role,
                    "type": sig_type,
                    "data": sig_data
                }
            }

            if to_client:
                # Direct Unicast to specified client_id
                room_conns = query_room_connections(room_code)
                for conn in room_conns:
                    if conn.get("client_id") == to_client:
                        post_to_conn(conn.get("connection_id"), payload)
            else:
                # Broadcast to everyone else in the room
                room_conns = query_room_connections(room_code)
                for conn in room_conns:
                    target_id = conn.get("connection_id")
                    if target_id != connection_id:
                        post_to_conn(target_id, payload)

    except Exception as e:
        logger.error(f"WebSocket custom handler failed: {e}")
        return {"statusCode": 500, "body": f"Error: {e}"}

    return {"statusCode": 200, "body": "OK"}


# HTTP REST API Handler
def handle_http(event):
    path = event.get("path", "")
    method = event.get("httpMethod", "GET")
    logger.info(f"REST Route: {method} {path}")

    # Standard JSON CORS Headers
    headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "POST,GET,OPTIONS"
    }

    if method == "OPTIONS":
        return {"statusCode": 200, "headers": headers, "body": ""}

    if path == "/health":
        return {"statusCode": 200, "headers": headers, "body": json.dumps({"status": "healthy"})}

    try:
        body = json.loads(event.get("body", "{}")) if event.get("body") else {}
    except Exception:
        body = {}

    # Endpoint: /api/register-room
    if path == "/api/register-room" and method == "POST":
        session_id = body.get("sessionId", "main")
        room_code = body.get("roomCode", "BTL1")
        signaling_url = body.get("signalingUrl", "")

        sessions_table.put_item(
            Item={
                "session_id": session_id,
                "room_code": room_code,
                "signaling_url": signaling_url,
                "updated_at": int(time.time())
            }
        )
        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps({"success": True, "message": f"Session {session_id} mapped to room {room_code}"})
        }

    # Endpoint: /api/webcam-upload
    elif path == "/api/webcam-upload" and method == "POST":
        session_id = body.get("sessionId", "main")
        role = body.get("role", "player1")
        image_base64 = body.get("image", "")

        # Write/Update base64 frame in DynamoDB session record
        update_expr = "SET latest_webcam_frame_p1 = :img, updated_at = :t" if role == "player1" else "SET latest_webcam_frame_p2 = :img, updated_at = :t"
        if role == "viewer" or not role:
            update_expr = "SET latest_webcam_frame = :img, updated_at = :t"

        try:
            sessions_table.update_item(
                Key={"session_id": session_id},
                UpdateExpression=update_expr,
                ExpressionAttributeValues={
                    ":img": image_base64,
                    ":t": int(time.time())
                }
            )
            return {
                "statusCode": 200,
                "headers": headers,
                "body": json.dumps({"success": True, "message": "Frame uploaded successfully"})
            }
        except Exception as e:
            logger.error(f"Error saving image: {e}")
            return {"statusCode": 500, "headers": headers, "body": json.dumps({"error": str(e)})}

    # Endpoint: /api/log
    elif path == "/api/log" and method == "POST":
        level = body.get("level", "INFO")
        message = body.get("message", "")
        logger.info(f"[BROWSER_LOG] [{level}] {message}")
        return {"statusCode": 200, "headers": headers, "body": json.dumps({"logged": True})}

    # Endpoint: /api/last-image
    elif path == "/api/last-image" and method == "GET":
        q_params = event.get("queryStringParameters", {}) or {}
        session_id = q_params.get("session_id", "main")
        role = q_params.get("role", "")

        resp = sessions_table.get_item(Key={"session_id": session_id})
        item = resp.get("Item", {})

        image_base64 = ""
        if role == "player1":
            image_base64 = item.get("latest_webcam_frame_p1", "")
        elif role == "player2":
            image_base64 = item.get("latest_webcam_frame_p2", "")
        else:
            image_base64 = item.get("latest_webcam_frame", item.get("latest_webcam_frame_p1", ""))

        html_headers = {"Content-Type": "text/html"}
        if not image_base64:
            return {
                "statusCode": 200,
                "headers": html_headers,
                "body": "<html><head><meta http-equiv='refresh' content='2'></head><body><h3>No webcam frame uploaded yet. Refreshing...</h3></body></html>"
            }

        html_content = f"""
        <html>
        <head>
            <title>Latest Webcam Capture</title>
            <meta http-equiv="refresh" content="2">
            <style>
                body {{
                    background: #111; color: #fff; text-align: center; font-family: sans-serif; margin: 0; padding: 20px;
                }}
                img {{
                    max-width: 95%; max-height: 85vh; border: 4px solid #FFFF00; border-radius: 12px; box-shadow: 0 0 30px rgba(255,255,0,0.2);
                }}
                h4 {{ color: #aaa; margin: 10px 0 0 0; letter-spacing: 2px; }}
            </style>
        </head>
        <body>
            <img src="data:image/jpeg;base64,{image_base64}">
            <h4>LIVE MATCH snapshot: {session_id} ({role or "active"})</h4>
        </body>
        </html>
        """
        return {"statusCode": 200, "headers": html_headers, "body": html_content}

    # Endpoint: /api/live-status
    elif path in ["/api/live-status", "/api/battle-result"] and method == "POST":
        session_id = body.get("sessionId", "main")
        room_code = body.get("roomCode", "BTL1")
        p1_score = body.get("p1Score", 0)
        p2_score = body.get("p2Score", 0)
        text_event = body.get("text", "")
        is_reset = body.get("isReset", False) or path == "/api/battle-result"

        logger.info(f"Live-status: session={session_id}, event={text_event}, reset={is_reset}")

        # Execute localized JJK translation
        translated_event = translate_detail(text_event)

        # Build prompt content block
        if path == "/api/battle-result":
            content_block = f"""
[BATTLE CONCLUSION TRIGGERED]
Final Match Results:
- Player 1 Score: {p1_score} points
- Player 2 Score: {p2_score} points
Summary description of final action: {translated_event}

Give a spectacular, sass-filled, high-octane commentary conclusion. Declare the victor or roast them both if it's a draw. Be Kugisaki Nobara, feisty and fashionable! Keep it to 2 sentences!
"""
        elif is_reset:
            content_block = f"""
[MATCH INITIAL GREETING]
Introduce yourself as the supreme JJK Commentator (Kugisaki Nobara). Give a high-energy, confident greeting to the competitors starting their duel in Room {room_code}. Tell them to prepare their cursed energy. Sassy, feisty, stylish! Keep it to 2 short sentences!
"""
        else:
            content_block = f"""
[MID-MATCH EVENT ENCOUNTERED]
Current Scores:
- Player 1 Score: {p1_score}
- Player 2 Score: {p2_score}
Latest Match Action: {translated_event}

React instantly to this specific action! Give sassy, feisty sorcerer trash-talk or hype up the battle with extreme energy. Speak directly to them like an arrogant fashion-lover. Keep it to 2 short, punchy sentences max!
"""

        # Try to retrieve the latest webcam frame for multimodal analysis
        image_bytes = None
        image_format = "jpeg"
        image_base64_raw = ""
        try:
            resp = sessions_table.get_item(Key={"session_id": session_id})
            item = resp.get("Item", {})
            img_b64 = item.get("latest_webcam_frame_p1", "") or item.get("latest_webcam_frame", "")
            if img_b64:
                # Strip prefix if it is a data URL
                if "," in img_b64:
                    header, img_b64_stripped = img_b64.split(",", 1)
                    if "png" in header:
                        image_format = "png"
                else:
                    img_b64_stripped = img_b64
                import base64
                image_bytes = base64.b64decode(img_b64_stripped)
                image_base64_raw = img_b64_stripped
                logger.info(f"Retrieved session webcam frame: {len(image_bytes)} bytes, format: {image_format}")
        except Exception as e:
            logger.warning(f"Failed to fetch session webcam frame for Bedrock: {e}")

        # Resolve Commentary Engine
        agent_engine = body.get("agent_type", DEFAULT_AGENT_TYPE)
        logger.info(f"Invoking Commentary Engine: {agent_engine}")

        commentary_text = ""

        if agent_engine == "strands_local":
            try:
                # Run Strands direct Bedrock invocation
                from strands import Agent
                from strands.models import BedrockModel

                system_prompt = load_system_prompt()
                model = BedrockModel(model_id=BEDROCK_MODEL_ID, region_name=BEDROCK_REGION, temperature=0.8)
                agent = Agent(
                    model=model,
                    system_prompt=system_prompt
                )
                import asyncio
                loop = asyncio.get_event_loop()
                
                # Support multimodal if image is present
                if image_bytes:
                    message_content = [
                        {"text": content_block},
                        {
                            "image": {
                                "format": image_format,
                                "source": {"bytes": image_bytes}
                            }
                        }
                    ]
                else:
                    message_content = content_block

                commentary_response = loop.run_until_complete(agent.invoke_async(message_content))
                commentary_text = str(commentary_response)
                logger.info(f"Strands Local commentary generated: {commentary_text}")
            except Exception as e:
                logger.error(f"Strands Local Engine failed, falling back to basic direct Converse request: {e}")
                commentary_text = direct_bedrock_fallback(content_block, image_bytes, image_format)

        elif agent_engine == "agentcore_runtime":
            try:
                # Invoke Amazon Bedrock AgentCore Runtime using boto3
                if not AGENTCORE_RUNTIME_ARN:
                    raise ValueError("AGENTCORE_RUNTIME_ARN environment variable is not defined")

                agent_client = boto3.client("bedrock-agentcore", region_name=BEDROCK_REGION)
                
                payload_dict = {"prompt": content_block, "session_id": session_id}
                if image_base64_raw:
                    payload_dict["image"] = image_base64_raw
                    payload_dict["image_format"] = image_format

                # Ensure runtimeSessionId is at least 33 characters to satisfy AWS validation rules
                import hashlib
                compliant_session_id = session_id
                if len(compliant_session_id) < 33:
                    compliant_session_id = hashlib.sha256(session_id.encode("utf-8")).hexdigest()

                response = agent_client.invoke_agent_runtime(
                    agentRuntimeArn=AGENTCORE_RUNTIME_ARN,
                    runtimeSessionId=compliant_session_id,
                    payload=json.dumps(payload_dict).encode("utf-8")
                )
                
                # Consume response stream
                chunks = []
                for chunk in response.get("response", []):
                    chunks.append(chunk.decode("utf-8"))
                
                agentcore_payload = json.loads("".join(chunks))
                commentary_text = agentcore_payload.get("response", "Sorcerer interference detected!")
                logger.info(f"AgentCore Runtime response generated: {commentary_text}")
            except Exception as e:
                logger.error(f"AgentCore Runtime call failed: {e}")
                commentary_text = direct_bedrock_fallback(content_block, image_bytes, image_format)

        else: # 'openclaw'
            # Default fallback to OpenClaw gateway
            try:
                import urllib3
                http = urllib3.PoolManager()
                url = f"{OPENCLAW_GATEWAY_URL}/v1/chat/completions"
                headers_api = {
                    "Content-Type": "application/json",
                    "x-openclaw-session-key": f"agent:{OPENCLAW_AGENT_ID}:domain-expansion-ar-game:{session_id}"
                }
                if OPENCLAW_TOKEN:
                    headers_api["Authorization"] = f"Bearer {OPENCLAW_TOKEN}"

                api_payload = {
                    "model": f"openclaw/{OPENCLAW_AGENT_ID}",
                    "messages": [{"role": "user", "content": content_block}],
                    "user": session_id
                }

                logger.info(f"Calling OpenClaw at URL: {url}")
                resp_api = http.request(
                    "POST",
                    url,
                    headers=headers_api,
                    body=json.dumps(api_payload),
                    timeout=30.0
                )
                if resp_api.status == 200:
                    resp_data = json.loads(resp_api.data.decode("utf-8"))
                    commentary_text = resp_data["choices"][0]["message"]["content"]
                    logger.info(f"OpenClaw response: {commentary_text}")
                else:
                    raise Exception(f"OpenClaw returned status code {resp_api.status}")
            except Exception as e:
                logger.error(f"OpenClaw Gateway call failed: {e}")
                commentary_text = direct_bedrock_fallback(content_block, image_bytes, image_format)

        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps({"commentary": commentary_text})
        }

    return {"statusCode": 404, "headers": headers, "body": json.dumps({"error": "Route not found"})}


def direct_bedrock_fallback(prompt: str, image_bytes: bytes = None, image_format: str = "jpeg") -> str:
    """Invokes Bedrock direct Converse API as ultimate robust fallback."""
    try:
        bedrock = boto3.client("bedrock-runtime", region_name=BEDROCK_REGION)
        system_prompt = load_system_prompt()
        
        # Converse payload structure with multimodal support
        content_list = [{"text": prompt}]
        if image_bytes:
            content_list.append({
                "image": {
                    "format": image_format,
                    "source": {"bytes": image_bytes}
                }
            })
            
        messages = [{"role": "user", "content": content_list}]
        system = [{"text": system_prompt}]
        
        response = bedrock.converse(
            modelId=BEDROCK_MODEL_ID,
            messages=messages,
            system=system,
            inferenceConfig={"temperature": 0.8, "maxTokens": 150}
        )
        output_text = response["output"]["message"]["content"][0]["text"]
        logger.info(f"Bedrock Direct Converse fallback completed: {output_text}")
        return output_text
    except Exception as e:
        logger.error(f"Bedrock Direct fallback failed: {e}")
        return "Show some cursed energy! Get moving or suffer my nails!"
