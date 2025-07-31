# Dog Robot Control Flow Documentation

## Complete Message Flow: MCP → IoT → PubSub → ActionExecutor → DogController

This document describes the complete flow of commands from the MCP server to the physical dog robot.

## Flow Overview

```
MCP Server → IoT Service → AWS IoT → PubSub Client → Action Executor → Dog Controller → Physical Robot
```

## Detailed Flow Steps

### 1. MCP Server (`mcp_server/index.py`)

**Input**: User calls MCP tool function
```python
dog_move_forward("dog_1", distance=100, speed=0.5)
```

**Processing**: 
- Maps MCP action names to executor action names
- Calls `robot_executor.execute_dog_action()`

**Output**: IoT message structure
```python
{
    "dogID": "dog_1",
    "action": "forward",  # Mapped from "move_forward"
    "parameters": {"distance": 100, "speed": 0.5}
}
```

### 2. IoT Service (`mcp_server/services/iot_service.py`)

**Input**: Message dictionary from MCP server

**Processing**:
- Converts message to JSON
- Publishes to AWS IoT topic: `dog_1/topic`

**Output**: JSON message published to IoT
```json
{
    "dogID": "dog_1",
    "action": "forward",
    "parameters": {"distance": 100, "speed": 0.5}
}
```

### 3. AWS IoT Core

**Processing**: Routes message to subscribed clients

### 4. PubSub Client (`robot_client/dog/pubsub.py`)

**Input**: IoT message from AWS IoT

**Processing**:
- Receives message via MQTT
- Parses JSON payload
- Extracts action and parameters
- Calls `executor.add_action_to_queue()`

**Code Flow**:
```python
def on_publish_received(self, publish_packet_data):
    payload = json.loads(publish_packet.payload)
    action_name = payload.get("action")
    parameters = payload.get("parameters", {})
    
    # Add to action executor queue
    self.executor.add_action_to_queue(action_name, parameters)
```

### 5. Action Executor (`robot_client/dog/action_executor.py`)

**Input**: Action name and parameters from PubSub

**Processing**:
- Validates action name against available actions
- Processes and validates parameters
- Adds action to execution queue
- Consumer thread executes actions sequentially

**Action Mapping**:
```python
actions = {
    "forward": {"type": "movement", "default_speed": 0.5},
    "back": {"type": "movement", "default_speed": 0.5},
    "left": {"type": "movement", "default_speed": 0.5},
    "right": {"type": "movement", "default_speed": 0.5},
    "cw": {"type": "rotation", "default_speed": 0.5},
    "ccw": {"type": "rotation", "default_speed": 0.5},
    # ... more actions
}
```

**Execution Flow**:
```python
def _execute_dog_action(self, action_name, parameters):
    if action_name == "forward":
        self.dog_controller.movement.move_forward(speed=speed, duration=duration)
    elif action_name == "back":
        self.dog_controller.movement.move_backward(speed=speed, duration=duration)
    # ... handle other actions
```

### 6. Dog Controller (`robot_client/dog/api/dog_controller.py`)

**Input**: Method calls from Action Executor

**Processing**:
- Provides high-level robot control interface
- Manages robot state (activation, walking mode, etc.)
- Delegates to MovementCommands and RobotStatus

**Example**:
```python
def move_forward(self, speed=0.5, duration=None):
    self.movement.move_forward(speed=speed, duration=duration)
```

### 7. Movement Commands (`robot_client/dog/api/movement_commands.py`)

**Input**: Movement method calls from Dog Controller

**Processing**:
- Converts high-level commands to UDP protocol
- Sends commands via UDP Publisher

**UDP Command Structure**:
```python
{
    'lx': 0.0, 'ly': 0.5,  # Left stick (movement)
    'rx': 0.0, 'ry': 0.0,  # Right stick
    'dpadx': 0, 'dpady': 0,  # D-pad (rotation/posture)
    'x': 0, 'square': 0, 'circle': 0, 'triangle': 0,  # Buttons
    'L1': 0, 'R1': 0, 'L2': 0, 'R2': 0,  # Shoulder buttons
    'message_rate': 20
}
```

### 8. Physical Robot

**Input**: UDP commands from Movement Commands

**Processing**: Robot hardware executes movement

## Action Name Mapping

### MCP Server → Action Executor

| MCP Action | Executor Action | Description |
|------------|-----------------|-------------|
| `move_forward` | `forward` | Move robot forward |
| `move_backward` | `back` | Move robot backward |
| `move_left` | `left` | Move robot left |
| `move_right` | `right` | Move robot right |
| `rotate_clockwise` | `cw` | Rotate clockwise |
| `rotate_counterclockwise` | `ccw` | Rotate counter-clockwise |
| `stand_up` | `stand_up` | Make robot stand up |
| `lay_down` | `lay_down` | Make robot lay down |
| `hop` | `hop` | Make robot hop |
| `activate` | `activate` | Toggle activation |
| `walk_mode` | `walk_mode` | Toggle walking mode |
| `dance_mode` | `dance_mode` | Toggle dancing mode |
| `stop` | `stop` | Stop all movement |
| `custom_movement` | `custom_movement` | Custom movement pattern |

### Executor Action → Dog Controller Method

| Executor Action | Dog Controller Method | Movement Commands Method |
|-----------------|----------------------|-------------------------|
| `forward` | `movement.move_forward()` | `move_forward()` |
| `back` | `movement.move_backward()` | `move_backward()` |
| `left` | `movement.move_left()` | `move_left()` |
| `right` | `movement.move_right()` | `move_right()` |
| `cw` | `movement.rotate_right()` | `rotate_right()` |
| `ccw` | `movement.rotate_left()` | `rotate_left()` |
| `stand_up` | `movement.stand_up()` | `stand_up()` |
| `lay_down` | `movement.lay_down()` | `lay_down()` |
| `hop` | `movement.hop()` | `hop()` |
| `activate` | `activate()` | `status.toggle_activation()` |
| `walk_mode` | `enable_walking()` | `status.toggle_walk()` |
| `dance_mode` | `enable_dancing()` | `status.toggle_dance()` |
| `stop` | `stop_all()` | `movement.stop()` |

## Parameter Flow

### Distance Parameter Example

1. **MCP Call**: `dog_move_forward("dog_1", distance=100, speed=0.5)`
2. **IoT Message**: `{"dogID": "dog_1", "action": "forward", "parameters": {"distance": 100, "speed": 0.5}}`
3. **Action Executor**: Processes parameters and calculates duration if needed
4. **Dog Controller**: `movement.move_forward(speed=0.5, duration=calculated_duration)`
5. **Movement Commands**: Sends UDP command with `ly=0.5` for specified duration

### Angle Parameter Example

1. **MCP Call**: `dog_rotate_right("dog_1", angle=90, speed=0.4)`
2. **IoT Message**: `{"dogID": "dog_1", "action": "cw", "parameters": {"angle": 90, "speed": 0.4}}`
3. **Action Executor**: Maps to clockwise rotation
4. **Dog Controller**: `movement.rotate_right(speed=0.4, duration=calculated_duration)`
5. **Movement Commands**: Sends UDP command with `dpadx=-0.4` for specified duration

## Error Handling

### Action Executor Level
- Validates action names against available actions
- Clamps speed parameters to valid range (0.1-1.0)
- Handles missing parameters with defaults
- Logs execution statistics

### Dog Controller Level
- Handles UDP communication errors
- Provides emergency stop functionality
- Maintains robot state consistency

### PubSub Level
- Handles JSON parsing errors
- Manages MQTT connection issues
- Supports both mTLS and WebSocket connections

## Configuration

### Robot IP and Port
```python
# In pubsub.py main()
executor = DogActionExecutor(
    robot_name=robot_name,
    robot_ip=settings.get("robot_ip", "192.168.137.195"),
    robot_port=settings.get("robot_port", 8830)
)
```

### IoT Topics
- Dog 1: `dog_1/topic`
- Dog 2: `dog_2/topic`
- All dogs: Publishes to all individual topics

## Testing

### Complete Flow Test
```bash
python robot_client/dog/test_complete_flow.py
```

### Individual Component Tests
```bash
python robot_client/dog/test_action_executor.py
python robot_client/dog/test_movement.py
```

## Troubleshooting

### Common Issues

1. **Action Not Found Error**
   - Check action name mapping in MCP server
   - Verify action exists in action_executor actions dictionary

2. **UDP Communication Issues**
   - Verify robot IP address in configuration
   - Check network connectivity to robot

3. **IoT Connection Issues**
   - Verify AWS credentials and certificates
   - Check IoT topic permissions

4. **Parameter Validation Errors**
   - Check parameter types and ranges
   - Verify required parameters are provided

### Debug Logging

Enable debug logging to trace the complete flow:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

This will show detailed logs for each step of the message flow.