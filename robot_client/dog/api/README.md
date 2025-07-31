# Dog Robot API

A clean, modular Python API for controlling dog robots through UDP communication.

## Overview

This API provides a structured interface for controlling dog robots, including movement commands, status management, and posture controls. The API is built on top of the UDPComms library and provides both high-level convenience methods and low-level control capabilities.

## Architecture

The API is organized into three main modules:

- **`DogController`**: Main controller class that orchestrates all robot operations
- **`MovementCommands`**: Handles all movement-related commands (forward, backward, rotation, etc.)
- **`RobotStatus`**: Manages robot status and mode controls (activation, walking mode, dancing mode)

## Quick Start

```python
from api import DogController

# Initialize the controller
dog = DogController(ip="192.168.137.195")

# Activate the robot
dog.activate()

# Enable walking mode
dog.enable_walking()

# Move forward for 2 seconds
dog.movement.move_forward(speed=0.5, duration=2.0)

# Stop all movement
dog.stop_all()
```

## API Reference

### DogController

The main controller class that provides high-level robot control.

#### Initialization

```python
dog = DogController(ip="192.168.137.195", port=8830)
```

#### Methods

- `activate()`: Toggle robot activation state
- `enable_walking()`: Toggle walking mode
- `enable_dancing()`: Toggle dancing mode
- `stop_all()`: Stop all movement
- `emergency_stop()`: Emergency stop with mode reset
- `get_status()`: Get current robot status

#### Properties

- `is_activated`: Check if robot is activated
- `is_walking_enabled`: Check if walking mode is enabled
- `is_dancing_enabled`: Check if dancing mode is enabled

### MovementCommands

Handles all movement-related operations.

#### Basic Movement

```python
# Move in cardinal directions
dog.movement.move_forward(speed=0.5, duration=2.0)
dog.movement.move_backward(speed=0.5, duration=2.0)
dog.movement.move_left(speed=0.5, duration=2.0)
dog.movement.move_right(speed=0.5, duration=2.0)

# Rotation
dog.movement.rotate_left(speed=0.5, duration=2.0)
dog.movement.rotate_right(speed=0.5, duration=2.0)
```

#### Posture Commands

```python
# Posture controls
dog.movement.stand_up(speed=0.5)
dog.movement.lay_down(speed=0.5)
dog.movement.hop(duration=1.0)
```

#### Custom Movement

```python
# Custom movement with full control
dog.movement.custom_movement(
    lx=0.3,     # Left stick X (-1.0 to 1.0)
    ly=0.3,     # Left stick Y (-1.0 to 1.0)
    rx=0.0,     # Right stick X (-1.0 to 1.0)
    ry=0.0,     # Right stick Y (-1.0 to 1.0)
    dpadx=0.0,  # D-pad X (-1.0 to 1.0)
    dpady=0.0,  # D-pad Y (-1.0 to 1.0)
    duration=2.0
)
```

#### Stop Movement

```python
dog.movement.stop()
```

### RobotStatus

Manages robot status and mode controls.

#### Status Controls

```python
# Toggle various modes
dog.status.toggle_activation()
dog.status.toggle_walk()
dog.status.toggle_dance()

# Special actions
dog.status.trigger_special_action()  # X button
dog.status.trigger_square_action()   # Square button
dog.status.trigger_triangle_action() # Triangle button
dog.status.trigger_l2_action()       # L2 button
dog.status.trigger_r2_action()       # R2 button
```

## Command Protocol

The API uses a standardized command protocol based on gamepad controls:

```python
{
    'lx': 0.0,      # Left stick X axis (-1.0 to 1.0)
    'ly': 0.0,      # Left stick Y axis (-1.0 to 1.0)
    'rx': 0.0,      # Right stick X axis (-1.0 to 1.0)
    'ry': 0.0,      # Right stick Y axis (-1.0 to 1.0)
    'x': 0,         # X button (0 or 1)
    'square': 0,    # Square button (0 or 1)
    'circle': 0,    # Circle button (0 or 1)
    'triangle': 0,  # Triangle button (0 or 1)
    'dpadx': 0,     # D-pad X axis (-1.0 to 1.0)
    'dpady': 0,     # D-pad Y axis (-1.0 to 1.0)
    'L1': 0,        # L1 button (0 or 1) - Activation toggle
    'R1': 0,        # R1 button (0 or 1) - Walking mode toggle
    'L2': 0,        # L2 button (0 or 1)
    'R2': 0,        # R2 button (0 or 1)
    'message_rate': 20  # Message rate
}
```

## Control Mapping

| Control | Function |
|---------|----------|
| Left Stick Y | Forward/Backward movement |
| Left Stick X | Left/Right movement |
| D-pad X | Rotation (left/right) |
| D-pad Y | Stand up/Lay down |
| L1 Button | Activation toggle |
| R1 Button | Walking mode toggle |
| Circle Button | Dancing mode toggle |
| X Button | Hop/Special action |

## Usage Examples

### Basic Movement Sequence

```python
from api import DogController
import time

dog = DogController()

# Setup
dog.activate()
dog.enable_walking()

# Movement sequence
dog.movement.move_forward(duration=2)
dog.movement.rotate_left(duration=1)
dog.movement.move_forward(duration=2)
dog.movement.rotate_right(duration=1)

# Cleanup
dog.stop_all()
```

### Status Monitoring

```python
dog = DogController()

# Check status
status = dog.get_status()
print(f"Robot status: {status}")

# Conditional operations
if not dog.is_activated:
    dog.activate()

if not dog.is_walking_enabled:
    dog.enable_walking()
```

### Error Handling

```python
try:
    dog = DogController(ip="192.168.137.195")
    dog.movement.move_forward(duration=2)
except Exception as e:
    print(f"Robot control error: {e}")
    dog.emergency_stop()
```

## Testing

The API includes comprehensive testing capabilities:

```bash
# Run interactive test mode
python test_movement.py --mode interactive

# Run comprehensive test suite
python test_movement.py --mode comprehensive

# Run basic movement tests
python test_movement.py --mode basic

# Legacy compatibility
python test_movement.py --mode legacy
```

## Dependencies

- `UDPComms`: UDP communication library
- `msgpack`: Message serialization
- `logging`: Python logging module
- `time`: Time utilities
- `typing`: Type hints

## Configuration

Default configuration:
- IP Address: `192.168.137.195`
- Port: `8830`
- Message Rate: `20 Hz`

These can be customized during initialization:

```python
dog = DogController(ip="192.168.1.100", port=9000)
```

## Safety Features

- **Speed Clamping**: All speed values are automatically clamped to valid ranges (-1.0 to 1.0)
- **Emergency Stop**: Immediate halt of all operations with mode reset
- **Error Handling**: Comprehensive error handling with logging
- **Status Tracking**: Real-time status monitoring and validation

## Logging

The API uses Python's logging module for debugging and monitoring:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

Log levels:
- `DEBUG`: Detailed command information
- `INFO`: General operation information
- `WARNING`: Warning messages
- `ERROR`: Error conditions

## Migration from Legacy Code

The new API maintains backward compatibility while providing improved structure:

### Old Code
```python
from api.UDPComms import Publisher

publisher = Publisher(8830, "192.168.137.195")
publisher.send({'lx': 0.5, 'ly': 0.0, ...})  # Manual command construction
```

### New Code
```python
from api import DogController

dog = DogController("192.168.137.195")
dog.movement.move_right(speed=0.5, duration=2.0)  # High-level interface
```

## Contributing

When extending the API:

1. Follow the existing module structure
2. Add comprehensive logging
3. Include error handling
4. Update tests and documentation
5. Maintain backward compatibility where possible