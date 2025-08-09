# Robot Service Documentation

## Overview

The `robot_service.py` module provides a comprehensive service for controlling different types of robots through AWS IoT. It has been updated to fully support the new dog robot system with enhanced parameter handling, action mapping, and error management.

## Architecture

```
Text Control Service
    ↓
Robot Service
    ↓
Publisher Classes (StandardRobotPublisher, DronePublisher, DogPublisher)
    ↓
AWS IoT Core
    ↓
Robot Clients (PubSub → ActionExecutor → DogController)
```

## Key Components

### 1. RobotService (Main Service Class)

The main service class that routes actions to appropriate publishers based on robot type.

**Key Methods:**

- `execute_robot_action(message, selected_robot, parameters)` - Main action execution method
- `execute_dog_action(dog_id, action, parameters)` - Direct dog action execution
- `process_actions(actions_list, robot, parameters)` - Sequential action processing
- `get_robot_status(robot_id)` - Get robot status information
- `validate_dog_action(action, parameters)` - Validate dog actions and parameters

### 2. DogPublisher (Enhanced for New Dog System)

Handles all dog robot communications with comprehensive action mapping.

**Features:**

- Complete action mapping for all dog capabilities
- Parameter validation and processing
- Support for movement, rotation, posture, status, and advanced actions
- Error handling and logging

**Supported Actions:**

#### Movement Actions

- `move_forward` → `forward`
- `move_backward` → `back`
- `move_left` → `left`
- `move_right` → `right`

#### Rotation Actions

- `rotate_clockwise` → `cw`
- `rotate_counterclockwise` → `ccw`
- `rotate_left` → `ccw`
- `rotate_right` → `cw`
- `turn_left` → `ccw`
- `turn_right` → `cw`
- `turn_back` → `cw` (with 180° angle)
- `turn_around` → `cw` (with 180° angle)

#### Posture Actions

- `stand_up` → `stand_up`
- `lay_down` → `lay_down`
- `hop` → `hop`

#### Status Actions

- `activate` → `activate`
- `enable_walking` → `walk_mode`
- `enable_dancing` → `dance_mode`
- `walk_mode` → `walk_mode`
- `dance_mode` → `dance_mode`

#### Control Actions

- `stop` → `stop`
- `emergency_stop` → `stop`

#### Advanced Actions

- `custom_movement` → `custom_movement`
- `circle_movement` → `custom_movement`

### 3. Parameter Processing

The service provides intelligent parameter processing with validation and defaults:

#### Movement Parameters

```python
{
    "distance": 50,    # cm (1-1000)
    "speed": 0.5       # 0.1-1.0
}
```

#### Rotation Parameters

```python
{
    "angle": 90,       # degrees (1-360)
    "speed": 0.5       # 0.1-1.0
}
```

#### Posture Parameters

```python
{
    "speed": 0.5       # 0.1-1.0
}
```

#### Special Action Parameters

```python
{
    "duration": 1.0    # seconds (0.1-5.0)
}
```

#### Advanced Movement Parameters

```python
{
    "lx": 0.0,         # Left stick X (-1.0 to 1.0)
    "ly": 0.0,         # Left stick Y (-1.0 to 1.0)
    "rx": 0.0,         # Right stick X (-1.0 to 1.0)
    "ry": 0.0,         # Right stick Y (-1.0 to 1.0)
    "dpadx": 0.0,      # D-pad X (-1.0 to 1.0)
    "dpady": 0.0,      # D-pad Y (-1.0 to 1.0)
    "duration": 2.0    # seconds (0.1-10.0)
}
```

## Usage Examples

### Basic Dog Movement

```python
from text_control.services.robot_service import robot_service

# Move dog forward 100cm at 60% speed
success = robot_service.execute_dog_action(
    dog_id="dog_1",
    action="move_forward",
    parameters={"distance": 100, "speed": 0.6}
)

# Rotate dog left 45 degrees
success = robot_service.execute_dog_action(
    dog_id="dog_1",
    action="rotate_left",
    parameters={"angle": 45, "speed": 0.4}
)
```

### Status Control

```python
# Activate dog
robot_service.execute_dog_action("dog_1", "activate")

# Enable walking mode
robot_service.execute_dog_action("dog_1", "walk_mode")

# Make dog stand up
robot_service.execute_dog_action("dog_1", "stand_up", {"speed": 0.5})
```

### Advanced Movement

```python
# Custom movement pattern
robot_service.execute_dog_action(
    dog_id="dog_1",
    action="custom_movement",
    parameters={
        "ly": 0.5,      # Forward
        "lx": 0.2,      # Right
        "dpadx": 0.1,   # Rotate left
        "duration": 3.0
    }
)
```

### Multiple Dogs

```python
# Execute action for all dogs
robot_service.execute_dog_action("all", "stand_up")

# Or use the general method
robot_service.execute_robot_action("stand_up", "dog_all")
```

### Action Validation

```python
# Validate action before execution
validation = robot_service.validate_dog_action(
    "move_forward",
    {"distance": 150, "speed": 0.7}
)

if validation["valid"]:
    robot_service.execute_dog_action("dog_1", "move_forward", parameters)
else:
    print(f"Invalid action: {validation['error']}")
```

## IoT Message Format

The service generates IoT messages in the format expected by the new dog system:

```json
{
  "dogID": "dog_1",
  "action": "forward",
  "parameters": {
    "distance": 100,
    "speed": 0.5
  }
}
```

**Topic Structure:**

- Individual dogs: `dog_1/topic`, `dog_2/topic`, `dog_3/topic`
- All dogs: Publishes to all individual topics in parallel

## Error Handling

The service provides comprehensive error handling:

### Parameter Validation

- Type checking and conversion
- Range validation with automatic clamping
- Default value assignment for missing parameters

### Network Error Handling

- Connection timeout handling
- Retry logic through AWS SDK configuration
- Graceful degradation on network issues

### Action Validation

- Supported action verification
- Parameter compatibility checking
- Detailed error messages

## Integration with New Dog System

The service is fully integrated with the new dog robot architecture:

### Message Flow

```
Text Control → Robot Service → AWS IoT → PubSub Client → Action Executor → Dog Controller → Physical Robot
```

### Action Mapping Chain

```
Service Action → SDK Action → Executor Action → Controller Method → UDP Command
```

### Example Flow

```
"move_forward" → "forward" → executor.add_action_to_queue("forward", params) → dog_controller.movement.move_forward() → UDP command
```

## Configuration

### Robot IDs

```python
DOG_IDS = ["dog_1", "dog_2", "dog_3"]
DRONE_IDS = ["drone_1", "drone_2"]
ROBOT_RANGE = range(1, 10)  # robot_1 to robot_9
```

### Default Parameters

```python
DEFAULT_DISTANCE = 50  # cm
DEFAULT_ANGLE = 90     # degrees
ACTION_DELAY = 0.1     # seconds between actions
```

### AWS IoT Configuration

```python
iot_client = boto3.client(
    "iot-data",
    config=Config(retries={"max_attempts": 3, "mode": "standard"}),
)
```

## Testing

### Run Service Tests

```bash
python text_control/test_robot_service.py
```

### Test Coverage

- Action mapping validation
- Parameter processing
- Message format generation
- Robot type routing
- Error handling scenarios

## Monitoring and Logging

The service provides detailed logging for:

- Action execution attempts
- Parameter validation results
- IoT message publishing
- Error conditions
- Performance metrics

### Log Levels

- `INFO`: Normal operation logging
- `WARNING`: Non-critical issues
- `ERROR`: Error conditions with details
- `DEBUG`: Detailed execution traces

## Best Practices

### Action Execution

1. Always validate actions before execution
2. Use appropriate parameters for better control
3. Handle return values to detect failures
4. Use batch operations for multiple robots

### Parameter Usage

1. Provide explicit parameters for predictable behavior
2. Use validation methods before execution
3. Handle parameter errors gracefully
4. Consider robot capabilities when setting parameters

### Error Handling

1. Check return values from all service methods
2. Use validation methods before execution
3. Implement retry logic for critical operations
4. Log errors for debugging and monitoring

## Migration from Legacy System

### Old Usage

```python
# Legacy approach
robot_service.execute_robot_action("dogMoveForward", "dog_1")
```

### New Usage

```python
# New approach with parameters
robot_service.execute_dog_action(
    "dog_1",
    "move_forward",
    {"distance": 100, "speed": 0.5}
)
```

### Benefits of New System

- Type-safe parameter handling
- Comprehensive action validation
- Better error reporting
- Enhanced logging and monitoring
- Direct integration with new dog API
- Support for advanced movement patterns

The updated robot service provides a robust, scalable, and maintainable interface for controlling the new dog robot system while maintaining backward compatibility with existing robot types.
