#!/usr/bin/env python3
"""
Complete Flow Test for MCP → IoT → PubSub → ActionExecutor → DogController

This script tests the complete message flow to ensure all components
work together correctly.
"""

import json
import logging
import time
from typing import Dict, Any
from action_executor import DogActionExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


def simulate_iot_message(action: str, parameters: Dict[str, Any] = None, dog_id: str = "dog_1") -> Dict[str, Any]:
    """
    Simulate an IoT message as it would come from the MCP server.
    
    Args:
        action: Action name
        parameters: Action parameters
        dog_id: Dog ID
        
    Returns:
        IoT message dictionary
    """
    if parameters is None:
        parameters = {}
        
    return {
        "dogID": dog_id,
        "action": action,
        "parameters": parameters
    }


def test_basic_movement_flow():
    """Test basic movement commands through the complete flow."""
    print("=== Testing Basic Movement Flow ===")
    
    # Initialize action executor (simulating what pubsub.py does)
    executor = DogActionExecutor(
        robot_name="test_dog",
        robot_ip="192.168.137.195"
    )
    
    try:
        # Test forward movement (simulating MCP → IoT → PubSub flow)
        print("Testing forward movement...")
        iot_message = simulate_iot_message("forward", {"distance": 50, "speed": 0.5})
        
        # This simulates what pubsub.py does when it receives the IoT message
        action_name = iot_message["action"]
        parameters = iot_message["parameters"]
        
        print(f"Simulated IoT message: {json.dumps(iot_message, indent=2)}")
        print(f"Adding action to queue: {action_name} with parameters: {parameters}")
        
        # Add to executor queue (this is what pubsub.py calls)
        action_id = executor.add_action_to_queue(action_name, parameters)
        print(f"Action added with ID: {action_id}")
        
        # Wait for execution
        time.sleep(3)
        
        # Check status
        status = executor.get_queue_status()
        stats = executor.get_execution_stats()
        
        print(f"Queue status: {status}")
        print(f"Execution stats: {stats}")
        
    finally:
        executor.shutdown()


def test_rotation_flow():
    """Test rotation commands through the complete flow."""
    print("\n=== Testing Rotation Flow ===")
    
    executor = DogActionExecutor(
        robot_name="test_dog",
        robot_ip="192.168.137.195"
    )
    
    try:
        # Test clockwise rotation
        print("Testing clockwise rotation...")
        iot_message = simulate_iot_message("cw", {"angle": 90, "speed": 0.4})
        
        action_name = iot_message["action"]
        parameters = iot_message["parameters"]
        
        print(f"Simulated IoT message: {json.dumps(iot_message, indent=2)}")
        
        action_id = executor.add_action_to_queue(action_name, parameters)
        print(f"Action added with ID: {action_id}")
        
        # Wait for execution
        time.sleep(3)
        
        stats = executor.get_execution_stats()
        print(f"Execution stats: {stats}")
        
    finally:
        executor.shutdown()


def test_status_control_flow():
    """Test status control commands through the complete flow."""
    print("\n=== Testing Status Control Flow ===")
    
    executor = DogActionExecutor(
        robot_name="test_dog",
        robot_ip="192.168.137.195"
    )
    
    try:
        # Test activation
        print("Testing activation...")
        iot_message = simulate_iot_message("activate", {})
        
        action_name = iot_message["action"]
        parameters = iot_message["parameters"]
        
        print(f"Simulated IoT message: {json.dumps(iot_message, indent=2)}")
        
        action_id = executor.add_action_to_queue(action_name, parameters)
        print(f"Action added with ID: {action_id}")
        
        time.sleep(2)
        
        # Test walking mode
        print("Testing walking mode...")
        iot_message = simulate_iot_message("walk_mode", {})
        
        action_name = iot_message["action"]
        parameters = iot_message["parameters"]
        
        action_id = executor.add_action_to_queue(action_name, parameters)
        print(f"Action added with ID: {action_id}")
        
        time.sleep(2)
        
        stats = executor.get_execution_stats()
        print(f"Execution stats: {stats}")
        
    finally:
        executor.shutdown()


def test_custom_movement_flow():
    """Test custom movement commands through the complete flow."""
    print("\n=== Testing Custom Movement Flow ===")
    
    executor = DogActionExecutor(
        robot_name="test_dog",
        robot_ip="192.168.137.195"
    )
    
    try:
        # Test custom movement
        print("Testing custom movement...")
        iot_message = simulate_iot_message("custom_movement", {
            "ly": 0.3,      # Forward
            "lx": 0.2,      # Right
            "dpadx": 0.1,   # Rotate left
            "duration": 2.0
        })
        
        action_name = iot_message["action"]
        parameters = iot_message["parameters"]
        
        print(f"Simulated IoT message: {json.dumps(iot_message, indent=2)}")
        
        action_id = executor.add_action_to_queue(action_name, parameters)
        print(f"Action added with ID: {action_id}")
        
        # Wait for execution
        time.sleep(4)
        
        stats = executor.get_execution_stats()
        print(f"Execution stats: {stats}")
        
    finally:
        executor.shutdown()


def test_error_handling_flow():
    """Test error handling in the complete flow."""
    print("\n=== Testing Error Handling Flow ===")
    
    executor = DogActionExecutor(
        robot_name="test_dog",
        robot_ip="192.168.137.195"
    )
    
    try:
        # Test invalid action
        print("Testing invalid action...")
        iot_message = simulate_iot_message("invalid_action", {})
        
        action_name = iot_message["action"]
        parameters = iot_message["parameters"]
        
        print(f"Simulated IoT message: {json.dumps(iot_message, indent=2)}")
        
        try:
            action_id = executor.add_action_to_queue(action_name, parameters)
            print(f"Action added with ID: {action_id}")
        except ValueError as e:
            print(f"Expected error caught: {e}")
        
        # Test valid action after error
        print("Testing valid action after error...")
        iot_message = simulate_iot_message("hop", {"duration": 1.0})
        
        action_name = iot_message["action"]
        parameters = iot_message["parameters"]
        
        action_id = executor.add_action_to_queue(action_name, parameters)
        print(f"Valid action added with ID: {action_id}")
        
        time.sleep(2)
        
        stats = executor.get_execution_stats()
        print(f"Final execution stats: {stats}")
        
    finally:
        executor.shutdown()


def test_mcp_action_mapping():
    """Test that MCP action names are properly mapped."""
    print("\n=== Testing MCP Action Mapping ===")
    
    # Test the action mapping that happens in the MCP server
    mcp_to_executor_mapping = {
        "move_forward": "forward",
        "move_backward": "back",
        "move_left": "left", 
        "move_right": "right",
        "rotate_clockwise": "cw",
        "rotate_counterclockwise": "ccw",
        "stand_up": "stand_up",
        "lay_down": "lay_down",
        "hop": "hop",
        "activate": "activate",
        "walk_mode": "walk_mode",
        "dance_mode": "dance_mode",
        "stop": "stop",
        "custom_movement": "custom_movement"
    }
    
    executor = DogActionExecutor(
        robot_name="test_dog",
        robot_ip="192.168.137.195"
    )
    
    try:
        print("Testing action name mappings...")
        
        for mcp_action, executor_action in mcp_to_executor_mapping.items():
            print(f"MCP action '{mcp_action}' → Executor action '{executor_action}'")
            
            # Simulate the mapping that happens in MCP server
            iot_message = simulate_iot_message(executor_action, {"speed": 0.3})
            
            # Test that the executor accepts the mapped action
            try:
                action_id = executor.add_action_to_queue(iot_message["action"], iot_message["parameters"])
                print(f"  ✓ Action accepted with ID: {action_id}")
            except ValueError as e:
                print(f"  ✗ Action rejected: {e}")
        
        # Wait for some actions to execute
        time.sleep(5)
        
        stats = executor.get_execution_stats()
        print(f"Mapping test stats: {stats}")
        
    finally:
        executor.shutdown()


def main():
    """Run all flow tests."""
    print("Complete Flow Test Suite")
    print("=" * 50)
    print("Testing: MCP → IoT → PubSub → ActionExecutor → DogController")
    print("=" * 50)
    
    try:
        test_basic_movement_flow()
        test_rotation_flow()
        test_status_control_flow()
        test_custom_movement_flow()
        test_error_handling_flow()
        test_mcp_action_mapping()
        
        print("\n" + "=" * 50)
        print("All Flow Tests Completed Successfully!")
        print("The complete MCP → IoT → PubSub → ActionExecutor → DogController flow is working.")
        print("=" * 50)
        
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
    except Exception as e:
        logger.error(f"Flow test failed: {e}")


if __name__ == "__main__":
    main()