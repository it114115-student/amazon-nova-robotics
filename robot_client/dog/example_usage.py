#!/usr/bin/env python3
"""
Dog Robot API Usage Examples

This script demonstrates how to use the new dog robot API for various
movement and control operations.
"""

import logging
import time

from api import DogController

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dog = DogController(ip="192.168.137.41", port=8830)


def enable_walking():
    # Initialize the dog controller

    # Enable walking mode
    print("Enabling walking mode...")
    dog.enable_walking()
    time.sleep(2)

    # # Enable walking mode
    # print("Enabling walking mode...")
    # dog.enable_walking()
    # time.sleep(2)


def basic_movement_example():
    """Demonstrate basic movement commands."""
    print("=== Basic Movement Example ===")

    # Initialize the dog controller
    # dog = DogController(ip="192.168.137.41", port=8830)

    # # Activate the robot
    # print("Activating robot...")
    # dog.activate()
    # time.sleep(2)

    # # Enable walking mode
    # print("Enabling walking mode...")
    # dog.enable_walking()
    # time.sleep(2)

    # Perform basic movements

    print("Moving backward...")
    dog.movement.move_backward(speed=1, duration=2.0)

    print("Moving forward...")
    dog.movement.move_forward(speed=1, duration=2.0)

    print("Moving left...")
    dog.movement.move_left(speed=1, duration=2.0)

    print("Moving right...")
    dog.movement.move_right(speed=1, duration=2.0)

    # Stop all movement
    print("Stopping...")
    dog.stop_all()

    # # Disable walking mode
    # print("Disabling walking mode...")
    # dog.enable_walking()


def rotation_example():
    """Demonstrate rotation commands."""
    print("\n=== Rotation Example ===")

    dog = DogController()

    print("Rotating left...")
    dog.movement.rotate_left(speed=1, duration=2.0)

    print("Rotating right...")
    dog.movement.rotate_right(speed=1, duration=2.0)

    dog.stop_all()


def posture_example():
    """Demonstrate posture commands."""
    print("\n=== Posture Example ===")

    dog = DogController()

    print("Standing up...")
    dog.movement.stand_up()
    time.sleep(2)

    print("Laying down...")
    dog.movement.lay_down()
    time.sleep(2)

    print("Hopping...")
    dog.movement.hop()


def custom_movement_example():
    """Demonstrate custom movement commands."""
    print("\n=== Custom Movement Example ===")

    dog = DogController()

    # Custom diagonal movement (forward + right)
    print("Custom diagonal movement...")
    dog.movement.custom_movement(
        lx=0.3, ly=0.3, duration=2.0  # Move right  # Move forward
    )

    # Custom rotation with forward movement
    print("Custom rotation + forward movement...")
    dog.movement.custom_movement(
        ly=0.2, dpadx=0.3, duration=3.0  # Slow forward  # Rotate left
    )

    dog.stop_all()


def status_monitoring_example():
    """Demonstrate status monitoring."""
    print("\n=== Status Monitoring Example ===")

    dog = DogController()

    # Check initial status
    status = dog.get_status()
    print(f"Initial status: {status}")

    # Activate and check status
    dog.activate()
    status = dog.get_status()
    print(f"After activation: {status}")

    # Enable walking and check status
    dog.enable_walking()
    status = dog.get_status()
    print(f"After enabling walking: {status}")

    # Enable dancing and check status
    dog.enable_dancing()
    status = dog.get_status()
    print(f"After enabling dancing: {status}")


def emergency_stop_example():
    """Demonstrate emergency stop functionality."""
    print("\n=== Emergency Stop Example ===")

    dog = DogController()

    # # Start some movement
    # print("Starting movement...")
    # dog.movement.move_forward(speed=0.5)

    # # Wait a bit
    # time.sleep(1)

    # Emergency stop
    print("EMERGENCY STOP!")
    dog.emergency_stop()

    # Check status
    status = dog.get_status()
    print(f"Status after emergency stop: {status}")


def main():
    """Run all examples."""
    try:
        print("Dog Robot API Usage Examples")
        print("=" * 40)

        enable_walking()
        # basic_movement_example()
        # Run examples
        # basic_movement_example()
        # rotation_example()
        # posture_example()
        # custom_movement_example()
        # status_monitoring_example()
        # emergency_stop_example()

        print("\n=== All Examples Completed ===")

    except KeyboardInterrupt:
        print("\nExamples interrupted by user")
    except Exception as e:
        logger.error(f"Example failed: {e}")


if __name__ == "__main__":
    main()
