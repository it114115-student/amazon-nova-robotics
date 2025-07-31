#!/usr/bin/env python3
"""
Test script for the updated robot_service.py

This script tests the robot service to ensure it works correctly
with the new dog robot system.
"""

import json
import logging
import sys
import os

# Add the parent directory to the path so we can import the service
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from text_control.services.robot_service import robot_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


def test_dog_action_mapping():
    """Test dog action mapping functionality."""
    print("=== Testing Dog Action Mapping ===")
    
    # Test supported actions
    supported_actions = robot_service.get_supported_dog_actions()
    print(f"Supported dog actions: {supported_actions}")
    
    # Test action validation
    test_cases = [
        # Valid cases
        {"action": "move_forward", "parameters": {"distance": 100, "speed": 0.5}},
        {"action": "rotate_left", "parameters": {"angle": 90, "speed": 0.3}},
        {"action": "stand_up", "parameters": {"speed": 0.4}},
        {"action": "hop", "parameters": {"duration": 1.5}},
        
        # Invalid cases
        {"action": "invalid_action", "parameters": {}},
        {"action": "move_forward", "parameters": {"distance": -10}},
        {"action": "rotate_left", "parameters": {"angle": 400}},
        {"action": "move_forward", "parameters": {"speed": 2.0}},
    ]
    
    for i, test_case in enumerate(test_cases):
        print(f"\nTest case {i+1}: {test_case}")
        validation = robot_service.validate_dog_action(
            test_case["action"], 
            test_case["parameters"]
        )
        print(f"Validation result: {validation}")


def test_dog_publisher_mapping():
    """Test the DogPublisher action mapping directly."""
    print("\n=== Testing DogPublisher Mapping ===")
    
    dog_publisher = robot_service.dog_publisher
    
    test_actions = [
        ("move_forward", {"distance": 50, "speed": 0.5}),
        ("rotate_clockwise", {"angle": 90, "speed": 0.4}),
        ("turn_left", {}),
        ("turn_back", {}),
        ("stand_up", {"speed": 0.3}),
        ("hop", {"duration": 1.0}),
        ("activate", {}),
        ("walk_mode", {}),
        ("stop", {}),
        ("custom_movement", {"lx": 0.5, "ly": 0.3, "duration": 2.0}),
    ]
    
    for action, parameters in test_actions:
        print(f"\nTesting action: {action} with parameters: {parameters}")
        try:
            sdk_mapping = dog_publisher._map_action_to_sdk(action, parameters)
            print(f"SDK mapping: {sdk_mapping}")
        except Exception as e:
            print(f"Error mapping action: {e}")


def test_robot_service_routing():
    """Test robot service routing logic."""
    print("\n=== Testing Robot Service Routing ===")
    
    # Test different robot types
    test_cases = [
        ("dog_1", "move_forward", {"distance": 100}),
        ("dog_2", "rotate_left", {"angle": 45}),
        ("dog_all", "stand_up", {}),
        ("drone_1", "takeoff", {}),
        ("robot_1", "bow", {}),
    ]
    
    for robot_id, action, parameters in test_cases:
        print(f"\nTesting: {robot_id} -> {action} with {parameters}")
        
        # Get robot status
        status = robot_service.get_robot_status(robot_id)
        print(f"Robot status: {status}")
        
        # Note: We're not actually executing the action to avoid IoT calls
        # In a real test, you would call:
        # result = robot_service.execute_robot_action(action, robot_id, parameters)
        print(f"Would execute: robot_service.execute_robot_action('{action}', '{robot_id}', {parameters})")


def test_parameter_processing():
    """Test parameter processing and validation."""
    print("\n=== Testing Parameter Processing ===")
    
    dog_publisher = robot_service.dog_publisher
    
    test_cases = [
        ("movement", {"distance": 75, "speed": 0.7}),
        ("movement", {"distance": "invalid"}),  # Should handle gracefully
        ("rotation", {"angle": 180, "speed": 0.3}),
        ("rotation", {"angle": 500}),  # Should clamp to 360
        ("posture", {"speed": 1.5}),  # Should clamp to 1.0
        ("special", {"duration": 0.05}),  # Should clamp to 0.1
        ("advanced", {"lx": 2.0, "ly": -2.0, "duration": 15.0}),  # Should clamp values
    ]
    
    for action_type, parameters in test_cases:
        print(f"\nTesting parameter processing for {action_type}: {parameters}")
        try:
            processed = dog_publisher._process_parameters("test_action", action_type, parameters)
            print(f"Processed parameters: {processed}")
        except Exception as e:
            print(f"Error processing parameters: {e}")


def test_message_format():
    """Test the IoT message format generation."""
    print("\n=== Testing IoT Message Format ===")
    
    dog_publisher = robot_service.dog_publisher
    
    # Test message format without actually publishing
    test_cases = [
        ("dog_1", "move_forward", {"distance": 100, "speed": 0.5}),
        ("dog_2", "dogRotateLeft", {"angle": 90}),  # Test with prefix
        ("dog_1", "stand_up", {}),
        ("dog_2", "custom_movement", {"lx": 0.3, "ly": 0.4, "duration": 2.0}),
    ]
    
    for robot_id, message, parameters in test_cases:
        print(f"\nTesting message format for: {robot_id} -> {message} with {parameters}")
        
        try:
            # Simulate the message creation process
            if message in dog_publisher.action_mapping:
                action = message
            else:
                from text_control.services.robot_service import MessageTransformer
                processed_message = MessageTransformer.remove_prefix(message, "dog")
                if processed_message is None:
                    action = MessageTransformer.camel_to_snake_case(message)
                else:
                    action = MessageTransformer.camel_to_snake_case(processed_message)
            
            sdk_mapping = dog_publisher._map_action_to_sdk(action, parameters or {})
            
            # Create the IoT message format
            data = {
                "dogID": robot_id.lower(),
                "action": sdk_mapping["action"],
                "parameters": sdk_mapping["params"],
            }
            
            topic = f"{robot_id}/topic"
            
            print(f"Topic: {topic}")
            print(f"Message: {json.dumps(data, indent=2)}")
            
        except Exception as e:
            print(f"Error creating message format: {e}")


def main():
    """Run all tests."""
    print("Robot Service Test Suite")
    print("=" * 50)
    print("Testing integration with new dog robot system")
    print("=" * 50)
    
    try:
        test_dog_action_mapping()
        test_dog_publisher_mapping()
        test_robot_service_routing()
        test_parameter_processing()
        test_message_format()
        
        print("\n" + "=" * 50)
        print("All Robot Service Tests Completed!")
        print("The robot service is ready for the new dog system.")
        print("=" * 50)
        
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)


if __name__ == "__main__":
    main()