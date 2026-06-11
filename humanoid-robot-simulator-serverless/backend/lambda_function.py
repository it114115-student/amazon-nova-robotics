import json
import os
import time
import logging
import boto3
from boto3.dynamodb.conditions import Key
from constants import HumanoidAction, DEFAULT_ROBOTS, ACTION_DURATIONS
from session_utils import decrypt, send_request

logger = logging.getLogger()
logger.setLevel(getattr(logging, os.environ.get("LOG_LEVEL", "INFO").upper(), logging.INFO))

CONNECTIONS_TABLE_NAME = os.environ.get('CONNECTIONS_TABLE', 'RobotSimulatorConnections')
SESSIONS_TABLE_NAME = os.environ.get('SESSIONS_TABLE', 'RobotSimulatorSessions')

dynamodb = boto3.resource('dynamodb')
connections_table = dynamodb.Table(CONNECTIONS_TABLE_NAME)
sessions_table = dynamodb.Table(SESSIONS_TABLE_NAME)

# --- DynamoDB State & Connections Persistence ---

def get_session_robots(session_key):
    """Retrieves session robots from DynamoDB or creates a default state if not found"""
    try:
        response = sessions_table.get_item(Key={'session_key': session_key})
        if 'Item' in response:
            robots_state = response['Item']['robots']
            # Run lazy evaluation to transition any expired actions back to idle
            return get_clean_robot_states(session_key, robots_state)
    except Exception as e:
        logger.error(f"❌ Error fetching session {session_key}: {e}")
        
    # If not found or error occurs, create default session robots
    robots = {}
    for config in DEFAULT_ROBOTS:
        robots[config['id']] = {
            'robot_id': config['id'],
            'position': config['position'].copy(),
            'rotation': [0.0, 0.0, 0.0],
            'color': config['color'],
            'current_action': 'idle',
            'action_start_time': 0.0,
            'action_duration': 0.0,
            'is_visible': True,
            'is_animating': False,
            'movement_count': 0
        }
    
    save_session_robots(session_key, robots)
    return robots


def save_session_robots(session_key, robots):
    """Saves session robots to DynamoDB"""
    try:
        now = int(time.time())
        # Convert floating point numbers to strings/decimals to prevent DynamoDB errors
        clean_robots = clean_floats_for_dynamodb(robots)
        sessions_table.put_item(
            Item={
                'session_key': session_key,
                'robots': clean_robots,
                'created_at': now,
                'updated_at': now
            }
        )
    except Exception as e:
        logger.error(f"❌ Error saving session {session_key}: {e}")


def get_clean_robot_states(session_key, robots):
    """Calculates active state based on elapsed time to expire actions dynamically (Lazy Threadless Evaluation)"""
    current_time = time.time()
    updated = False
    
    for robot_id, robot in robots.items():
        # Read floats safely
        is_animating = robot.get('is_animating', False)
        current_action = robot.get('current_action', 'idle')
        
        if is_animating and current_action != 'idle':
            start_time = float(robot.get('action_start_time', 0.0))
            duration = float(robot.get('action_duration', 2.0))
            
            # If the current time is past start_time + duration, transition back to idle
            if current_time > (start_time + duration):
                robot['is_animating'] = False
                robot['current_action'] = 'idle'
                updated = True
                
    if updated:
        save_session_robots(session_key, robots)
        
    return robots


def clean_floats_for_dynamodb(data):
    """Recursively converts floats to strings/decimals for DynamoDB storage compatibility"""
    # Simply mapping floats to strings or converting to float/int is easiest.
    # Since Three.js client-side parses numeric JSON, converting float types to strings is okay,
    # or we can simply rely on boto3's standard JSON parsing or float representations.
    # Decimal type from decimal import Decimal is best for DynamoDB, but returning floats to client is easier.
    # To keep it standard, let's cast float numbers to python float or Decimal. 
    # Boto3 DynamoDB resource accepts floats if they are exact, but floats can cause precision errors.
    # Let's convert floats in list/dicts to python floats or Decimals.
    from decimal import Decimal
    if isinstance(data, float):
        # Round or convert to Decimal
        return Decimal(str(round(data, 4)))
    elif isinstance(data, dict):
        return {k: clean_floats_for_dynamodb(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_floats_for_dynamodb(x) for x in data]
    return data


def convert_decimals_to_floats(data):
    """Recursively converts Decimal objects back to float for JSON responses"""
    from decimal import Decimal
    if isinstance(data, Decimal):
        return float(data)
    elif isinstance(data, dict):
        return {k: convert_decimals_to_floats(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_decimals_to_floats(x) for x in data]
    return data


# --- Connection Tracking Persistence ---

def save_connection(connection_id, session_key):
    try:
        connections_table.put_item(
            Item={
                'connection_id': connection_id,
                'session_key': session_key,
                'connected_at': int(time.time())
            }
        )
        logger.info(f"💾 Saved connection {connection_id} linked to session {session_key}")
    except Exception as e:
        logger.error(f"❌ Error saving connection: {e}")


def delete_connection(connection_id):
    try:
        connections_table.delete_item(Key={'connection_id': connection_id})
        logger.info(f"🗑️ Deleted connection {connection_id}")
    except Exception as e:
        logger.error(f"❌ Error deleting connection: {e}")


def get_session_connections(session_key):
    """Queries GSI on session_key to find all active WebSocket connection IDs"""
    try:
        response = connections_table.query(
            IndexName='SessionKeyIndex',
            KeyConditionExpression=Key('session_key').eq(session_key)
        )
        return [item['connection_id'] for item in response.get('Items', [])]
    except Exception as e:
        logger.error(f"❌ Error querying connections GSI for session {session_key}: {e}")
        return []


# --- API Gateway Callback Broadcasting ---

def post_to_connections(event, session_key, payload):
    """Sends a JSON payload to all active WebSocket clients joined to this session"""
    conn_ids = get_session_connections(session_key)
    if not conn_ids:
        logger.info(f"No active connection IDs found for session {session_key}")
        return

    endpoint_url = os.environ.get("WEBSOCKET_ENDPOINT")
    if not endpoint_url:
        request_context = event.get('requestContext', {})
        domain_name = request_context.get('domainName')
        stage = request_context.get('stage')
        
        if not domain_name or not stage:
            logger.warning("⚠️ No domainName or stage in requestContext. Cannot send callbacks.")
            return

        endpoint_url = f"https://{domain_name}/{stage}"

    if endpoint_url.startswith("wss://"):
        endpoint_url = endpoint_url.replace("wss://", "https://")

    apigw_client = boto3.client('apigatewaymanagementapi', endpoint_url=endpoint_url)
    
    # Ensure payload contains standard float formats for client JSON decoding
    clean_payload = convert_decimals_to_floats(payload)
    payload_str = json.dumps(clean_payload)
    
    for cid in conn_ids:
        try:
            apigw_client.post_to_connection(ConnectionId=cid, Data=payload_str)
        except apigw_client.exceptions.GoneException:
            logger.info(f"🗑️ Clean up gone connection: {cid}")
            delete_connection(cid)
        except Exception as e:
            logger.error(f"❌ Error posting callback to {cid}: {e}")


def post_to_single_connection(event, connection_id, payload):
    """Sends a JSON payload to a specific single WebSocket connection ID"""
    endpoint_url = os.environ.get("WEBSOCKET_ENDPOINT")
    if not endpoint_url:
        request_context = event.get('requestContext', {})
        domain_name = request_context.get('domainName')
        stage = request_context.get('stage')
        endpoint_url = f"https://{domain_name}/{stage}"

    if endpoint_url.startswith("wss://"):
        endpoint_url = endpoint_url.replace("wss://", "https://")
    
    apigw_client = boto3.client('apigatewaymanagementapi', endpoint_url=endpoint_url)
    clean_payload = convert_decimals_to_floats(payload)
    
    try:
        apigw_client.post_to_connection(ConnectionId=connection_id, Data=json.dumps(clean_payload))
    except Exception as e:
        logger.error(f"❌ Error posting callback to connection {connection_id}: {e}")


# --- Helper Router Routing ---

def get_session_key_from_event(event):
    """Extracts session_key dynamically from query strings, headers, or JSON body"""
    query_params = event.get('queryStringParameters') or {}
    if 'session_key' in query_params:
        return query_params['session_key']
    if 'session-key' in query_params:
        return query_params['session-key']
        
    headers = event.get('headers') or {}
    for k, v in headers.items():
        if k.lower() in ('x-session-key', 'session_key', 'session-key'):
            return v
            
    body_str = event.get('body')
    if body_str:
        try:
            body = json.loads(body_str)
            if isinstance(body, dict):
                return body.get('session_key') or body.get('session-key')
        except:
            pass
            
    return None


def make_rest_response(status_code, body):
    """Constructs API Gateway compatible HTTP REST response with CORS headers"""
    clean_body = convert_decimals_to_floats(body)
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization,X-Requested-With",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS"
        },
        "body": json.dumps(clean_body)
    }


# --- REST API Routing & Handlers ---

def handle_rest_request(event):
    """Processes HTTP requests (REST API endpoints)"""
    path = event.get('rawPath', event.get('path', ''))
    method = event.get('requestContext', {}).get('http', {}).get('method', event.get('httpMethod', 'GET')).upper()
    
    logger.info(f"🌐 Handling HTTP REST Request: Method={method}, Path={path}")
    
    # 1. CORS Preflight OPTIONS Handling
    if method == "OPTIONS":
        return make_rest_response(200, {"success": True})
        
    # 2. Health check route
    if path == "/health":
        return make_rest_response(200, {"status": "healthy", "service": "robot-simulator-serverless"})
        
    # Extract session key and fetch state
    session_key = get_session_key_from_event(event)
    if not session_key and path != "/api/status":
        return make_rest_response(400, {"success": False, "error": "Session key required"})
        
    # 3. GET /api/status route
    if path == "/api/status":
        if session_key:
            robots = get_session_robots(session_key)
            return make_rest_response(200, {
                "server": "running",
                "session_key": session_key,
                "robots_count": len(robots),
                "actions": [action.value for action in HumanoidAction],
                "animating_robots": [
                    robot_id for robot_id, r in robots.items() if r.get('is_animating', False)
                ]
            })
        else:
            return make_rest_response(200, {
                "server": "running",
                "session_required": True,
                "actions": [action.value for action in HumanoidAction]
            })
            
    # 4. GET /api/robots
    if path == "/api/robots" and method == "GET":
        robots = get_session_robots(session_key)
        return make_rest_response(200, {
            "success": True,
            "session_key": session_key,
            "robot_count": len(robots),
            "robots": robots
        })
        
    # 5. POST /api/add_robot/<robot_id>
    if path.startswith("/api/add_robot/") and method == "POST":
        robot_id = path.split("/")[-1]
        body = {}
        if event.get('body'):
            try:
                body = json.loads(event['body'])
            except:
                pass
                
        robots = get_session_robots(session_key)
        if robot_id in robots:
            return make_rest_response(400, {"success": False, "error": f"Robot {robot_id} already exists"})
            
        new_robot = {
            'robot_id': robot_id,
            'position': body.get('position', [0.0, 0.0, 0.0]),
            'rotation': [0.0, 0.0, 0.0],
            'color': body.get('color', '#4A90E2'),
            'current_action': 'idle',
            'action_start_time': 0.0,
            'action_duration': 0.0,
            'is_visible': True,
            'is_animating': False,
            'movement_count': 0
        }
        robots[robot_id] = new_robot
        save_session_robots(session_key, robots)
        
        # Broadcast additions
        post_to_connections(event, session_key, {
            "type": "robot_added",
            "data": {"robot_id": robot_id, "robot_data": new_robot}
        })
        return make_rest_response(200, {"success": True, "robot_id": robot_id, "robot_data": new_robot})
        
    # 6. DELETE /api/remove_robot/<robot_id>
    if path.startswith("/api/remove_robot/") and method == "DELETE":
        robot_id = path.split("/")[-1]
        robots = get_session_robots(session_key)
        
        if robot_id == "all":
            removed_robots = list(robots.keys())
            robots.clear()
            save_session_robots(session_key, robots)
            post_to_connections(event, session_key, {
                "type": "robots_removed_all",
                "data": {"removed_robots": removed_robots}
            })
            return make_rest_response(200, {"success": True, "removed_robots": removed_robots})
        elif robot_id in robots:
            del robots[robot_id]
            save_session_robots(session_key, robots)
            post_to_connections(event, session_key, {
                "type": "robot_removed",
                "data": {"removed_robot": robot_id}
            })
            return make_rest_response(200, {"success": True, "robot_id": robot_id})
        else:
            return make_rest_response(404, {"success": False, "error": f"Robot {robot_id} not found"})
            
    # 7. POST /api/reset_robots
    if path == "/api/reset_robots" and method == "POST":
        robots = get_session_robots(session_key)
        robots.clear()
        for config in DEFAULT_ROBOTS:
            robots[config['id']] = {
                'robot_id': config['id'],
                'position': config['position'].copy(),
                'rotation': [0.0, 0.0, 0.0],
                'color': config['color'],
                'current_action': 'idle',
                'action_start_time': 0.0,
                'action_duration': 0.0,
                'is_visible': True,
                'is_animating': False,
                'movement_count': 0
            }
        save_session_robots(session_key, robots)
        post_to_connections(event, session_key, {
            "type": "robots_reset",
            "data": {"robots": robots}
        })
        return make_rest_response(200, {"success": True, "robots": robots})
        
    # 8. POST /run_action/<robot_id>
    if path.startswith("/run_action/") and method == "POST":
        robot_id = path.split("/")[-1]
        body = {}
        if event.get('body'):
            try:
                body = json.loads(event['body'])
            except:
                pass
                
        action = body.get("action")
        if not action:
            return make_rest_response(400, {"success": False, "error": "Action is required"})
            
        robots = get_session_robots(session_key)
        if robot_id != "all" and robot_id not in robots:
            return make_rest_response(404, {"success": False, "error": f"Robot {robot_id} not found"})
            
        duration = ACTION_DURATIONS.get(action, 2.0)
        current_time = time.time()
        
        # Trigger action updates
        if robot_id == "all":
            for r_id, r in robots.items():
                r['current_action'] = action
                r['action_start_time'] = current_time
                r['action_duration'] = duration
                r['is_animating'] = True
                r['movement_count'] = r.get('movement_count', 0) + 1
        else:
            r = robots[robot_id]
            r['current_action'] = action
            r['action_start_time'] = current_time
            r['action_duration'] = duration
            r['is_animating'] = True
            r['movement_count'] = r.get('movement_count', 0) + 1
            
        save_session_robots(session_key, robots)
        
        # Dispatch hardware execution
        handle_real_robot_commands(session_key, robots, action, robot_id)
        
        # Broadcast events
        post_to_connections(event, session_key, {
            "type": "actions",
            "data": {"session_key": session_key, "action_name": action, "robot_id": robot_id}
        })
        post_to_connections(event, session_key, {
            "type": "robot_states",
            "data": robots
        })
        
        return make_rest_response(200, {
            "success": True,
            "robot_id": robot_id,
            "action": action,
            "robots_affected": list(robots.keys()) if robot_id == "all" else [robot_id],
            "message": f"Action '{action}' triggered"
        })
        
    # 9. POST /speech/<robot_id>
    if path.startswith("/speech/") and method == "POST":
        robot_id = path.split("/")[-1]
        body = {}
        if event.get('body'):
            try:
                body = json.loads(event['body'])
            except:
                pass
                
        audio_url = body.get("audio_url")
        text = body.get("text", "")
        
        if not audio_url:
            return make_rest_response(400, {"success": False, "error": "audio_url is required"})
            
        post_to_connections(event, session_key, {
            "type": "speech",
            "data": {
                "audio_url": audio_url,
                "text": text,
                "robot_id": robot_id,
                "session_key": session_key
            }
        })
        return make_rest_response(200, {"success": True, "robot_id": robot_id, "message": "Speech audio broadcast"})

    # 9b. POST /api/digital-human/speak
    if path == "/api/digital-human/speak" and method == "POST":
        body = {}
        if event.get('body'):
            try:
                body = json.loads(event['body'])
            except:
                pass
                
        message = body.get("message", "")
        audio_url = body.get("audio_url", "")
        if not message:
            return make_rest_response(400, {"success": False, "error": "message is required"})
            
        post_to_connections(event, session_key or "mcpserver", {
            "type": "digital_human_speech",
            "data": {
                "message": message,
                "audio_url": audio_url,
                "session_key": session_key or "mcpserver"
            }
        })
        return make_rest_response(200, {"success": True, "message": "Digital human speech broadcasted"})

    # 10. POST /api/video/change_source
    if path == "/api/video/change_source" and method == "POST":
        body = {}
        if event.get('body'):
            try:
                body = json.loads(event['body'])
            except:
                pass
        video_src = body.get("video_src")
        if not video_src:
            return make_rest_response(400, {"success": False, "error": "video_src is required"})
            
        post_to_connections(event, session_key, {
            "type": "video_source_changed",
            "data": {"video_src": video_src, "session_key": session_key}
        })
        return make_rest_response(200, {"success": True, "video_src": video_src, "session_key": session_key})

    # 11. POST /api/video/control
    if path == "/api/video/control" and method == "POST":
        body = {}
        if event.get('body'):
            try:
                body = json.loads(event['body'])
            except:
                pass
        action = body.get("action")
        if action not in ["play", "pause", "toggle"]:
            return make_rest_response(400, {"success": False, "error": "Invalid action. Must be play, pause, or toggle"})
            
        post_to_connections(event, session_key, {
            "type": "video_control",
            "data": {"action": action, "session_key": session_key}
        })
        return make_rest_response(200, {"success": True, "action": action, "session_key": session_key})

    # 12. GET /api/video/status
    if path == "/api/video/status" and method == "GET":
        return make_rest_response(200, {
            "success": True,
            "session_key": session_key,
            "available_videos": ["/static/video/prog-video-01.mp4"],
            "supported_actions": ["play", "pause", "toggle"],
            "supported_endpoints": {
                "change_source": "/api/video/change_source",
                "control": "/api/video/control"
            }
        })
        
    return make_rest_response(404, {"success": False, "error": f"Endpoint {path} not found"})


def handle_real_robot_commands(session_key, robots, action, target_robot_id):
    """Forward command invocation to actual hardware robots if the session key is decrypted as valid"""
    try:
        real_robot_session = decrypt(session_key)
        if not real_robot_session or not real_robot_session.get("is_valid"):
            return
            
        logger.info(f"✅ Session key validated for real robot control: {real_robot_session}")
        
        if target_robot_id == "all" and real_robot_session.get("robot") == "all":
            for r_id in robots.keys():
                send_request(method="RunAction", robot_id=r_id, action=action)
        elif real_robot_session.get("robot") == "all" and target_robot_id != "all":
            send_request(method="RunAction", robot_id=target_robot_id, action=action)
        elif real_robot_session.get("robot") == target_robot_id:
            send_request(method="RunAction", robot_id=target_robot_id, action=action)
    except Exception as e:
        logger.error(f"❌ Error dispatching commands to real robots: {e}")


# --- WebSocket API Events & Custom Handlers ---

def handle_websocket_event(event, connection_id):
    """Processes WebSocket connection management and messages"""
    route_key = event.get('requestContext', {}).get('routeKey')
    
    logger.info(f"🔌 Handling WebSocket Event: Route={route_key}, ConnectionId={connection_id}")
    
    # 1. $connect Event
    if route_key == "$connect":
        session_key = get_session_key_from_event(event)
        if session_key:
            save_connection(connection_id, session_key)
            return {"statusCode": 200, "body": "Connected"}
        # Allow connecting, but let them join_session in default route if they missed the query parameter
        return {"statusCode": 200, "body": "Connected"}
        
    # 2. $disconnect Event
    if route_key == "$disconnect":
        delete_connection(connection_id)
        return {"statusCode": 200, "body": "Disconnected"}
        
    # 3. $default Message Routing (custom client requests)
    if route_key == "$default":
        body_str = event.get('body', '{}')
        try:
            body = json.loads(body_str)
        except Exception as e:
            logger.error(f"Failed to parse WebSocket JSON payload: {e}")
            return {"statusCode": 400, "body": "Invalid JSON"}
            
        action = body.get('action')
        session_key = body.get('session_key') or get_session_key_from_event(event)
        
        if not session_key:
            post_to_single_connection(event, connection_id, {
                "type": "error", "data": {"message": "session_key is required"}
            })
            return {"statusCode": 200, "body": "Missing Session Key"}
            
        logger.info(f"📥 WebSocket Msg Action={action} on Session={session_key}")
        
        # Ensure connection mappings are updated dynamically on action messages
        save_connection(connection_id, session_key)
        
        # Route standard action commands
        if action == "join_session" or action == "get_robot_states":
            robots = get_session_robots(session_key)
            post_to_single_connection(event, connection_id, {
                "type": "robot_states", "data": robots
            })
            return {"statusCode": 200, "body": "States Returned"}
            
        elif action == "robot_action" or action == "actions":
            robot_id = body.get('robot_id', 'all')
            action_name = body.get('action', body.get('action_name', 'idle'))
            
            robots = get_session_robots(session_key)
            if robot_id != "all" and robot_id not in robots:
                post_to_single_connection(event, connection_id, {
                    "type": "action_result", 
                    "data": {"status": "error", "message": f"Robot {robot_id} not found"}
                })
                return {"statusCode": 200}
                
            duration = ACTION_DURATIONS.get(action_name, 2.0)
            current_time = time.time()
            
            if robot_id == "all":
                for r_id, r in robots.items():
                    r['current_action'] = action_name
                    r['action_start_time'] = current_time
                    r['action_duration'] = duration
                    r['is_animating'] = True
                    r['movement_count'] = r.get('movement_count', 0) + 1
                result = {"status": "success", "robot_id": "all", "action": action_name}
            else:
                r = robots[robot_id]
                r['current_action'] = action_name
                r['action_start_time'] = current_time
                r['action_duration'] = duration
                r['is_animating'] = True
                r['movement_count'] = r.get('movement_count', 0) + 1
                result = {"status": "success", "robot_id": robot_id, "action": action_name}
                
            save_session_robots(session_key, robots)
            
            # Dispatch commands to real robots if authorized
            handle_real_robot_commands(session_key, robots, action_name, robot_id)
            
            # Broadcast results
            post_to_single_connection(event, connection_id, {"type": "action_result", "data": result})
            post_to_connections(event, session_key, {"type": "robot_states", "data": robots})
            
        elif action == "reset_session":
            robots = get_session_robots(session_key)
            robots.clear()
            for config in DEFAULT_ROBOTS:
                robots[config['id']] = {
                    'robot_id': config['id'],
                    'position': config['position'].copy(),
                    'rotation': [0.0, 0.0, 0.0],
                    'color': config['color'],
                    'current_action': 'idle',
                    'action_start_time': 0.0,
                    'action_duration': 0.0,
                    'is_visible': True,
                    'is_animating': False,
                    'movement_count': 0
                }
            save_session_robots(session_key, robots)
            post_to_single_connection(event, connection_id, {
                "type": "reset_result", "data": {"status": "success", "message": "Session reset successfully"}
            })
            post_to_connections(event, session_key, {"type": "robot_states", "data": robots})
            
        elif action == "change_video_source":
            video_src = body.get("video_src")
            if not video_src:
                return {"statusCode": 200}
                
            post_to_connections(event, session_key, {
                "type": "video_source_changed",
                "data": {"video_src": video_src, "session_key": session_key}
            })
            post_to_single_connection(event, connection_id, {
                "type": "video_source_change_result", 
                "data": {"status": "success", "video_src": video_src, "message": f"Video source changed"}
            })
            
        elif action == "speech":
            audio_url = body.get("audio_url")
            text = body.get("text", "")
            robot_id = body.get("robot_id", "all")
            
            if not audio_url:
                return {"statusCode": 200}
                
            post_to_connections(event, session_key, {
                "type": "speech",
                "data": {
                    "audio_url": audio_url,
                    "text": text,
                    "robot_id": robot_id,
                    "session_key": session_key
                }
            })
            post_to_single_connection(event, connection_id, {
                "type": "speech_result",
                "data": {"status": "success", "message": "Speech audio broadcasted"}
            })
            
        elif action == "control_video":
            video_action = body.get("action")
            if video_action not in ["play", "pause", "toggle"]:
                return {"statusCode": 200}
                
            post_to_connections(event, session_key, {
                "type": "video_control",
                "data": {"action": video_action, "session_key": session_key}
            })
            post_to_single_connection(event, connection_id, {
                "type": "video_control_result",
                "data": {"status": "success", "action": video_action, "message": f"Video {video_action} command sent"}
            })
            
        elif action == "camera_control":
            # Pass through camera control coordinates directly
            post_to_connections(event, session_key, {
                "type": "camera_control",
                "data": body
            })
            
        return {"statusCode": 200, "body": "Processed"}
        
    return {"statusCode": 404, "body": "WebSocket Route Not Found"}


# --- Monolithic Handler Entrypoint ---

def lambda_handler(event, context):
    """Entry point for both HTTP and WebSocket integrations"""

    try:
        request_context = event.get('requestContext', {})
        connection_id = request_context.get('connectionId')
        
        # Route to WebSocket handler if connectionId is present
        if connection_id:
            return handle_websocket_event(event, connection_id)
            
        # Otherwise route to HTTP REST API handler
        return handle_rest_request(event)
    except Exception as e:
        logger.critical(f"💥 Critical Serverless Exception: {e}", exc_info=True)
        return make_rest_response(500, {"success": False, "error": "Internal Server Error", "details": str(e)})
