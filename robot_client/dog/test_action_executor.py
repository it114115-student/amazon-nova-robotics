#!/usr/bin/env python3
"""
Test script for the enhanced DogActionExecutor

This script demonstrates and tests the functionality of the updated
action executor with the new dog API integration.
"""

import time
import logging
from action_executor import DogActionExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


def test_basic_actions():
    """Test basic action execution."""
    print("=== Testing Basic Actions ===")
    
    # Initialize executor
    executor = DogActionExecutor(
        robot_name="test_dog",
        robot_ip="192.168.137.195"
    )
    
    try:
        # Test adding actions to queue
        print("Adding actions to queue...")
        
        # Basic movement actions
        executor.add_action_to_queue("forward", {"speed": 0.3, "duration": 2.0})
        executor.add_action_to_queue("left", {"speed": 0.3, "duration": 1.5})
        executor.add_action_to_queue("back", {"speed": 0.3, "duration": 2.0})
        executor.add_action_to_queue("right", {"speed": 0.3, "duration": 1.5})
        
        # Rotation actions
        executor.add_action_to_queue("cw", {"speed": 0.4, "duration": 1.0})
        executor.add_action_to_queue("ccw", {"speed": 0.4, "duration": 1.0})
        
        # Wait for actions to complete
        print("Waiting for actions to complete...")
        while executor.is_running or not executor.action_queue.empty():
            status = executor.get_queue_status()
            print(f"Queue size: {status['queue_size']}, Running: {status['is_running']}")
            time.sleep(1)
        
        # Print execution statistics
        stats = executor.get_execution_stats()
        print(f"Execution stats: {stats}")
        
    finally:
        executor.shutdown()


def test_parameter_handling():
    """Test parameter processing and validation."""
    print("\n=== Testing Parameter Handling ===")
    
    executor = DogActionExecutor(
        robot_name="test_dog",
        robot_ip="192.168.137.195"
    )
    
    try:
        # Test with distance parameter
        print("Testing distance-based movement...")
        executor.add_action_to_queue("forward", {"distance": 100})  # Should auto-calculate duration
        
        # Test with angle parameter
        print("Testing angle-based rotation...")
        executor.add_action_to_queue("cw", {"angle": 90})  # Should auto-calculate duration
        
        # Test parameter validation (speed clamping)
        print("Testing parameter validation...")
        executor.add_action_to_queue("left", {"speed": 2.0})  # Should be clamped to 1.0
        executor.add_action_to_queue("right", {"speed": -0.5})  # Should be clamped to 0.1
        
        # Wait for completion
        time.sleep(2)
        while executor.is_running:
            time.sleep(0.5)
        
        stats = executor.get_execution_stats()
        print(f"Parameter test stats: {stats}")
        
    finally:
        executor.shutdown()


def test_status_actions():
    """Test status control actions."""
    print("\n=== Testing Status Actions ===")
    
    executor = DogActionExecutor(
        robot_name="test_dog",
        robot_ip="192.168.137.195"
    )
    
    try:
        # Test status actions
        print("Testing activation...")
        executor.add_action_to_queue("activate")
        
        print("Testing walk mode...")
        executor.add_action_to_queue("walk_mode")
        
        print("Testing posture actions...")
        executor.add_action_to_queue("stand_up")
        time.sleep(2)
        executor.add_action_to_queue("hop")
        time.sleep(2)
        executor.add_action_to_queue("lay_down")
        
        # Wait for completion
        while executor.is_running or not executor.action_queue.empty():
            time.sleep(0.5)
        
        # Get final status
        status = executor.get_queue_status()
        print(f"Final robot status: {status.get('robot_status')}")
        
    finally:
        executor.shutdown()


def test_queue_management():
    """Test queue management features."""
    print("\n=== Testing Queue Management ===")
    
    executor = DogActionExecutor(
        robot_name="test_dog",
        robot_ip="192.168.137.195"
    )
    
    try:
        # Add multiple actions
        print("Adding multiple actions...")
        for i in range(5):
            executor.add_action_to_queue("forward", {"duration": 1.0})
        
        # Check queue status
        status = executor.get_queue_status()
        print(f"Queue size after adding: {status['queue_size']}")
        
        # Test pause/resume
        time.sleep(2)  # Let one action start
        print("Pausing execution...")
        executor.pause_execution()
        
        time.sleep(2)
        print("Resuming execution...")
        executor.resume_execution()
        
        # Test emergency stop
        time.sleep(1)
        print("Testing emergency stop...")
        executor.stop()
        
        # Check final status
        final_status = executor.get_queue_status()
        print(f"Final queue size: {final_status['queue_size']}")
        
    finally:
        executor.shutdown()


def test_error_handling():
    """Test error handling capabilities."""
    print("\n=== Testing Error Handling ===")
    
    executor = DogActionExecutor(
        robot_name="test_dog",
        robot_ip="192.168.137.195"
    )
    
    try:
        # Test invalid action
        print("Testing invalid action...")
        try:
            executor.add_action_to_queue("invalid_action")
        except ValueError as e:
            print(f"Caught expected error: {e}")
        
        # Test available actions
        available = executor.get_available_actions()
        print(f"Available actions: {list(available.keys())}")
        
        # Add a valid action to ensure system still works
        executor.add_action_to_queue("hop")
        
        # Wait for completion
        while executor.is_running:
            time.sleep(0.5)
        
        stats = executor.get_execution_stats()
        print(f"Error handling test stats: {stats}")
        
    finally:
        executor.shutdown()


def main():
    """Run all tests."""
    print("Dog Action Executor Test Suite")
    print("=" * 40)
    
    try:
        test_basic_actions()
        test_parameter_handling()
        test_status_actions()
        test_queue_management()
        test_error_handling()
        
        print("\n=== All Tests Completed ===")
        
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
    except Exception as e:
        logger.error(f"Test failed: {e}")


if __name__ == "__main__":
    main()