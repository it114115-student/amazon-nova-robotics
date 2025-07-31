#!/usr/bin/env python3
"""
Test script for the refactored dog robot control system.

This script demonstrates the improved architecture, configuration management,
and utility functions of the refactored dog robot control system.
"""

import logging
import time
from typing import Dict, Any

from api import DogController
from action_executor import DogActionExecutor
from config import (
    DEFAULT_ROBOT_IP, 
    DEFAULT_ROBOT_PORT,
    ActionType,
    validate_speed,
    validate_duration
)
from utils import (
    ParameterValidator,
    StatisticsTracker,
    setup_logging,
    retry_on_exception
)

# Setup logging
setup_logging(level="INFO")
logger = logging.getLogger(__name__)


class RefactoredSystemTester:
    """Test class for the refactored dog robot system."""
    
    def __init__(self, robot_ip: str = DEFAULT_ROBOT_IP, robot_port: int = DEFAULT_ROBOT_PORT):
        """
        Initialize the tester.
        
        Args:
            robot_ip: Robot IP address
            robot_port: Robot port
        """
        self.robot_ip = robot_ip
        self.robot_port = robot_port
        self.dog_controller = None
        self.action_executor = None
        self.stats_tracker = StatisticsTracker()
        
    def setup_controllers(self) -> None:
        """Setup dog controller and action executor."""
        logger.info("Setting up controllers...")
        
        try:
            # Initialize dog controller
            self.dog_controller = DogController(ip=self.robot_ip, port=self.robot_port)
            logger.info("Dog controller initialized successfully")
            
            # Initialize action executor
            self.action_executor = DogActionExecutor(
                robot_name="test_dog",
                robot_ip=self.robot_ip,
                robot_port=self.robot_port
            )
            logger.info("Action executor initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup controllers: {e}")
            raise
    
    def test_parameter_validation(self) -> None:
        """Test parameter validation utilities."""
        logger.info("Testing parameter validation...")
        
        validator = ParameterValidator()
        
        # Test speed validation
        assert validator.validate_speed(0.5) == 0.5
        assert validator.validate_speed(-1.0) == 0.1  # Clamped to minimum
        assert validator.validate_speed(2.0) == 1.0   # Clamped to maximum
        
        # Test duration validation
        assert validator.validate_duration(2.0) == 2.0
        assert validator.validate_duration(0.05) == 0.1  # Clamped to minimum
        assert validator.validate_duration(20.0) == 10.0  # Clamped to maximum
        
        # Test axis value validation
        assert validator.validate_axis_value(0.5) == 0.5
        assert validator.validate_axis_value(-2.0) == -1.0  # Clamped
        assert validator.validate_axis_value(2.0) == 1.0    # Clamped
        
        logger.info("Parameter validation tests passed")
    
    def test_configuration_usage(self) -> None:
        """Test configuration module usage."""
        logger.info("Testing configuration usage...")
        
        # Test validation functions
        speed = validate_speed(0.7)
        assert 0.1 <= speed <= 1.0
        
        duration = validate_duration(3.0)
        assert 0.1 <= duration <= 10.0
        
        logger.info("Configuration usage tests passed")
    
    def test_statistics_tracking(self) -> None:
        """Test statistics tracking."""
        logger.info("Testing statistics tracking...")
        
        # Record some actions
        self.stats_tracker.record_action_start("forward")
        time.sleep(0.1)
        self.stats_tracker.record_action_success("forward")
        
        self.stats_tracker.record_action_start("left")
        time.sleep(0.1)
        self.stats_tracker.record_action_failure("left", "Test failure")
        
        # Get statistics
        stats = self.stats_tracker.get_statistics()
        assert stats["total_actions"] == 2
        assert stats["successful_actions"] == 1
        assert stats["failed_actions"] == 1
        assert stats["success_rate"] == 50.0
        
        logger.info("Statistics tracking tests passed")
    
    def test_basic_movements(self) -> None:
        """Test basic movement commands."""
        if not self.dog_controller:
            logger.warning("Dog controller not available, skipping movement tests")
            return
            
        logger.info("Testing basic movements...")
        
        try:
            # Test forward movement
            logger.info("Testing forward movement...")
            self.dog_controller.movement.move_forward(speed=0.3, duration=1.0)
            
            # Test backward movement
            logger.info("Testing backward movement...")
            self.dog_controller.movement.move_backward(speed=0.3, duration=1.0)
            
            # Test left movement
            logger.info("Testing left movement...")
            self.dog_controller.movement.move_left(speed=0.3, duration=1.0)
            
            # Test right movement
            logger.info("Testing right movement...")
            self.dog_controller.movement.move_right(speed=0.3, duration=1.0)
            
            # Stop all movement
            self.dog_controller.stop_all()
            
            logger.info("Basic movement tests completed")
            
        except Exception as e:
            logger.error(f"Movement test failed: {e}")
    
    def test_action_executor(self) -> None:
        """Test action executor functionality."""
        if not self.action_executor:
            logger.warning("Action executor not available, skipping tests")
            return
            
        logger.info("Testing action executor...")
        
        try:
            # Test adding actions to queue
            action_id1 = self.action_executor.add_action_to_queue("forward", {"speed": 0.3, "duration": 1.0})
            action_id2 = self.action_executor.add_action_to_queue("left", {"speed": 0.3, "duration": 1.0})
            
            logger.info(f"Added actions: {action_id1}, {action_id2}")
            
            # Wait for actions to complete
            time.sleep(3.0)
            
            # Get queue status
            status = self.action_executor.get_queue_status()
            logger.info(f"Queue status: {status}")
            
            # Get execution statistics
            stats = self.action_executor.get_execution_stats()
            logger.info(f"Execution stats: {stats}")
            
            logger.info("Action executor tests completed")
            
        except Exception as e:
            logger.error(f"Action executor test failed: {e}")
    
    def test_error_handling(self) -> None:
        """Test error handling and recovery."""
        logger.info("Testing error handling...")
        
        try:
            # Test invalid action
            if self.action_executor:
                try:
                    self.action_executor.add_action_to_queue("invalid_action")
                    assert False, "Should have raised ValueError"
                except ValueError as e:
                    logger.info(f"Correctly caught invalid action error: {e}")
            
            # Test parameter validation errors
            validator = ParameterValidator()
            try:
                validator.validate_speed("invalid")
                assert False, "Should have raised ValueError"
            except ValueError as e:
                logger.info(f"Correctly caught parameter validation error: {e}")
            
            logger.info("Error handling tests passed")
            
        except Exception as e:
            logger.error(f"Error handling test failed: {e}")
    
    def test_retry_mechanism(self) -> None:
        """Test retry mechanism."""
        logger.info("Testing retry mechanism...")
        
        # Test function that fails twice then succeeds
        attempt_count = 0
        def failing_function():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise Exception(f"Attempt {attempt_count} failed")
            return "Success"
        
        try:
            result = retry_on_exception(failing_function, max_retries=3, delay=0.1)
            assert result == "Success"
            assert attempt_count == 3
            logger.info("Retry mechanism test passed")
        except Exception as e:
            logger.error(f"Retry mechanism test failed: {e}")
    
    def run_all_tests(self) -> None:
        """Run all tests."""
        logger.info("Starting refactored system tests...")
        
        try:
            # Setup
            self.setup_controllers()
            
            # Run tests
            self.test_parameter_validation()
            self.test_configuration_usage()
            self.test_statistics_tracking()
            self.test_error_handling()
            self.test_retry_mechanism()
            
            # Run integration tests if controllers are available
            self.test_basic_movements()
            self.test_action_executor()
            
            logger.info("All tests completed successfully!")
            
        except Exception as e:
            logger.error(f"Test suite failed: {e}")
            raise
        finally:
            # Cleanup
            if self.action_executor:
                self.action_executor.shutdown()
    
    def cleanup(self) -> None:
        """Cleanup resources."""
        logger.info("Cleaning up...")
        if self.action_executor:
            self.action_executor.shutdown()


def main():
    """Main test function."""
    # You can customize the robot IP and port here
    robot_ip = "192.168.137.195"  # Change to your robot's IP
    robot_port = 8830
    
    tester = RefactoredSystemTester(robot_ip=robot_ip, robot_port=robot_port)
    
    try:
        tester.run_all_tests()
    except KeyboardInterrupt:
        logger.info("Tests interrupted by user")
    except Exception as e:
        logger.error(f"Test suite failed: {e}")
    finally:
        tester.cleanup()


if __name__ == "__main__":
    main()