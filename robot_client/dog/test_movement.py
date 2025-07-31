"""
Dog Robot Movement Testing Module

This module provides comprehensive testing capabilities for dog robot movements,
including individual movement tests, sequence tests, and interactive testing modes.
"""

import time
import logging
import argparse
import sys
from typing import List, Dict, Any, Optional, Callable
from api import DogController

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


class MovementTester:
    """Comprehensive movement testing class for dog robots."""
    
    def __init__(self, ip: str = "192.168.137.195", port: int = 8830):
        """
        Initialize the movement tester.
        
        Args:
            ip: Robot IP address
            port: UDP communication port
        """
        self.dog = DogController(ip, port)
        self.test_results: List[Dict[str, Any]] = []
        logger.info(f"Movement tester initialized for robot at {ip}:{port}")
    
    def _log_test_result(self, test_name: str, success: bool, 
                        duration: float, error: Optional[str] = None) -> None:
        """Log test result for later analysis."""
        result = {
            'test_name': test_name,
            'success': success,
            'duration': duration,
            'timestamp': time.time(),
            'error': error
        }
        self.test_results.append(result)
        
        status = "PASS" if success else "FAIL"
        logger.info(f"Test {test_name}: {status} (Duration: {duration:.2f}s)")
        if error:
            logger.error(f"Test {test_name} error: {error}")
    
    def _execute_test(self, test_name: str, test_func: Callable, 
                     *args, **kwargs) -> bool:
        """
        Execute a test function with error handling and timing.
        
        Args:
            test_name: Name of the test
            test_func: Function to execute
            *args, **kwargs: Arguments for the test function
            
        Returns:
            True if test passed, False otherwise
        """
        start_time = time.time()
        try:
            test_func(*args, **kwargs)
            duration = time.time() - start_time
            self._log_test_result(test_name, True, duration)
            return True
        except Exception as e:
            duration = time.time() - start_time
            self._log_test_result(test_name, False, duration, str(e))
            return False

def test_movements():
    dog = DogController()
    
    # Test sequence
    print("Starting test sequence...")
    time.sleep(2)  # Give time to get ready
    
    # The activate command should be at least run once to activate the Controller, run again to deactivate
    # print("Activating dog...")
    # dog.activateToggle()
    # time.sleep(1)  # Wait for activation

    # For walking, need to run once to start the walking motion, run again to stop
    # print("Walk toggle...")
    # dog.walkToggle()
    # time.sleep(1)

    # After enable walking motion, change the movement by forward, backward, left, right
    # print("Testing forward...")
    # dog.move_forward(1)
    # time.sleep(1)
    
    # After enable walking motion, change the movement by forward, backward, left, right
    # print("Testing backward...")
    # dog.move_backward(1)
    # time.sleep(1)
    
    # After enable walking motion, change the movement by forward, backward, left, right
    # print("Testing left...")
    # dog.move_left(1)
    # time.sleep(1)
    
    # After enable walking motion, change the movement by forward, backward, left, right
    # print("Testing right...")
    # dog.move_right(1)
    # time.sleep(1)

    # print("Dance toggle...")
    # dog.danceToggle()
    # time.sleep(1)

    # print("Testing stand up...")
    # dog.stand_up()
    # time.sleep(1)

    # print("Testing lay down...")
    # dog.lay_down()
    # time.sleep(1)

    # print("Dance toggle...")
    # dog.danceToggle()
    # time.sleep(1)

    # print("Walk toggle...")
    # dog.walkToggle()
    # time.sleep(1)

    # print("Rotate left...")
    # dog.rotateLeft()
    # time.sleep(1)

    # print("Hop...")
    # dog.hop()
    # time.sleep(1)
    
    print("Test complete!")

if __name__ == "__main__":
    test_movements()  
  def test_basic_movements(self, duration: float = 1.0) -> Dict[str, bool]:
        """
        Test all basic movement commands.
        
        Args:
            duration: Duration for each movement test
            
        Returns:
            Dictionary of test results
        """
        logger.info("Starting basic movement tests...")
        results = {}
        
        # Test forward movement
        results['forward'] = self._execute_test(
            "forward_movement", 
            self.dog.movement.move_forward, 
            duration=duration
        )
        time.sleep(0.5)
        
        # Test backward movement
        results['backward'] = self._execute_test(
            "backward_movement", 
            self.dog.movement.move_backward, 
            duration=duration
        )
        time.sleep(0.5)
        
        # Test left movement
        results['left'] = self._execute_test(
            "left_movement", 
            self.dog.movement.move_left, 
            duration=duration
        )
        time.sleep(0.5)
        
        # Test right movement
        results['right'] = self._execute_test(
            "right_movement", 
            self.dog.movement.move_right, 
            duration=duration
        )
        time.sleep(0.5)
        
        # Test rotations
        results['rotate_left'] = self._execute_test(
            "rotate_left", 
            self.dog.movement.rotate_left, 
            duration=duration
        )
        time.sleep(0.5)
        
        results['rotate_right'] = self._execute_test(
            "rotate_right", 
            self.dog.movement.rotate_right, 
            duration=duration
        )
        time.sleep(0.5)
        
        logger.info(f"Basic movement tests completed. Results: {results}")
        return results
    
    def test_posture_commands(self) -> Dict[str, bool]:
        """
        Test posture-related commands.
        
        Returns:
            Dictionary of test results
        """
        logger.info("Starting posture tests...")
        results = {}
        
        # Test stand up
        results['stand_up'] = self._execute_test(
            "stand_up", 
            self.dog.movement.stand_up
        )
        time.sleep(2)
        
        # Test lay down
        results['lay_down'] = self._execute_test(
            "lay_down", 
            self.dog.movement.lay_down
        )
        time.sleep(2)
        
        # Test hop
        results['hop'] = self._execute_test(
            "hop", 
            self.dog.movement.hop
        )
        time.sleep(1)
        
        logger.info(f"Posture tests completed. Results: {results}")
        return results
    
    def test_status_controls(self) -> Dict[str, bool]:
        """
        Test status control commands.
        
        Returns:
            Dictionary of test results
        """
        logger.info("Starting status control tests...")
        results = {}
        
        # Test activation toggle
        results['activation'] = self._execute_test(
            "activation_toggle", 
            self.dog.activate
        )
        time.sleep(1)
        
        # Test walking mode toggle
        results['walking_mode'] = self._execute_test(
            "walking_mode_toggle", 
            self.dog.enable_walking
        )
        time.sleep(1)
        
        # Test dancing mode toggle
        results['dancing_mode'] = self._execute_test(
            "dancing_mode_toggle", 
            self.dog.enable_dancing
        )
        time.sleep(1)
        
        logger.info(f"Status control tests completed. Results: {results}")
        return results
    
    def test_emergency_stop(self) -> bool:
        """
        Test emergency stop functionality.
        
        Returns:
            True if test passed, False otherwise
        """
        logger.info("Testing emergency stop...")
        
        # Start some movement
        self.dog.movement.move_forward(speed=0.3)
        time.sleep(0.5)
        
        # Execute emergency stop
        result = self._execute_test(
            "emergency_stop", 
            self.dog.emergency_stop
        )
        
        time.sleep(1)
        return result
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """
        Run a comprehensive test suite covering all functionality.
        
        Returns:
            Complete test results
        """
        logger.info("Starting comprehensive test suite...")
        
        comprehensive_results = {
            'basic_movements': self.test_basic_movements(),
            'posture_commands': self.test_posture_commands(),
            'status_controls': self.test_status_controls(),
            'emergency_stop': self.test_emergency_stop()
        }
        
        # Calculate overall statistics
        total_tests = 0
        passed_tests = 0
        
        for category, results in comprehensive_results.items():
            if isinstance(results, dict):
                for test_result in results.values():
                    total_tests += 1
                    if test_result:
                        passed_tests += 1
            else:
                total_tests += 1
                if results:
                    passed_tests += 1
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        comprehensive_results['summary'] = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': total_tests - passed_tests,
            'success_rate': success_rate
        }
        
        logger.info(f"Comprehensive test completed. Success rate: {success_rate:.1f}%")
        return comprehensive_results
    
    def interactive_test_mode(self) -> None:
        """Run interactive test mode allowing manual command execution."""
        logger.info("Starting interactive test mode...")
        print("\n=== Dog Robot Interactive Test Mode ===")
        print("Available commands:")
        print("  1. forward [speed] [duration] - Move forward")
        print("  2. backward [speed] [duration] - Move backward")
        print("  3. left [speed] [duration] - Move left")
        print("  4. right [speed] [duration] - Move right")
        print("  5. rotate_left [speed] [duration] - Rotate left")
        print("  6. rotate_right [speed] [duration] - Rotate right")
        print("  7. stand_up - Stand up")
        print("  8. lay_down - Lay down")
        print("  9. hop - Hop")
        print("  10. activate - Toggle activation")
        print("  11. walk_mode - Toggle walking mode")
        print("  12. dance_mode - Toggle dancing mode")
        print("  13. stop - Stop all movement")
        print("  14. emergency - Emergency stop")
        print("  15. status - Show robot status")
        print("  16. quit - Exit interactive mode")
        print()
        
        while True:
            try:
                command = input("Enter command: ").strip().lower().split()
                if not command:
                    continue
                
                cmd = command[0]
                
                if cmd == 'quit':
                    break
                elif cmd == 'forward':
                    speed = float(command[1]) if len(command) > 1 else 0.5
                    duration = float(command[2]) if len(command) > 2 else None
                    self.dog.movement.move_forward(speed, duration)
                elif cmd == 'backward':
                    speed = float(command[1]) if len(command) > 1 else 0.5
                    duration = float(command[2]) if len(command) > 2 else None
                    self.dog.movement.move_backward(speed, duration)
                elif cmd == 'left':
                    speed = float(command[1]) if len(command) > 1 else 0.5
                    duration = float(command[2]) if len(command) > 2 else None
                    self.dog.movement.move_left(speed, duration)
                elif cmd == 'right':
                    speed = float(command[1]) if len(command) > 1 else 0.5
                    duration = float(command[2]) if len(command) > 2 else None
                    self.dog.movement.move_right(speed, duration)
                elif cmd == 'rotate_left':
                    speed = float(command[1]) if len(command) > 1 else 0.5
                    duration = float(command[2]) if len(command) > 2 else None
                    self.dog.movement.rotate_left(speed, duration)
                elif cmd == 'rotate_right':
                    speed = float(command[1]) if len(command) > 1 else 0.5
                    duration = float(command[2]) if len(command) > 2 else None
                    self.dog.movement.rotate_right(speed, duration)
                elif cmd == 'stand_up':
                    self.dog.movement.stand_up()
                elif cmd == 'lay_down':
                    self.dog.movement.lay_down()
                elif cmd == 'hop':
                    self.dog.movement.hop()
                elif cmd == 'activate':
                    self.dog.activate()
                elif cmd == 'walk_mode':
                    self.dog.enable_walking()
                elif cmd == 'dance_mode':
                    self.dog.enable_dancing()
                elif cmd == 'stop':
                    self.dog.stop_all()
                elif cmd == 'emergency':
                    self.dog.emergency_stop()
                elif cmd == 'status':
                    status = self.dog.get_status()
                    print(f"Robot Status: {status}")
                else:
                    print(f"Unknown command: {cmd}")
                    
            except KeyboardInterrupt:
                print("\nExiting interactive mode...")
                break
            except Exception as e:
                print(f"Error executing command: {e}")
        
        logger.info("Interactive test mode ended")
    
    def get_test_report(self) -> str:
        """
        Generate a detailed test report.
        
        Returns:
            Formatted test report string
        """
        if not self.test_results:
            return "No tests have been executed yet."
        
        report = "\n=== Dog Robot Movement Test Report ===\n"
        report += f"Total tests executed: {len(self.test_results)}\n"
        
        passed = sum(1 for result in self.test_results if result['success'])
        failed = len(self.test_results) - passed
        success_rate = (passed / len(self.test_results)) * 100
        
        report += f"Passed: {passed}\n"
        report += f"Failed: {failed}\n"
        report += f"Success rate: {success_rate:.1f}%\n\n"
        
        report += "Detailed Results:\n"
        for result in self.test_results:
            status = "PASS" if result['success'] else "FAIL"
            report += f"  {result['test_name']}: {status} ({result['duration']:.2f}s)\n"
            if result['error']:
                report += f"    Error: {result['error']}\n"
        
        return report


def run_predefined_sequence() -> None:
    """Run a predefined test sequence (legacy compatibility)."""
    logger.info("Running predefined test sequence...")
    tester = MovementTester()
    
    print("Starting test sequence...")
    time.sleep(2)  # Give time to get ready
    
    # Example sequence - uncomment as needed
    print("Testing basic movements...")
    tester.test_basic_movements(duration=1.0)
    
    print("Testing posture commands...")
    tester.test_posture_commands()
    
    print("Test sequence complete!")


def main():
    """Main function with command line argument parsing."""
    parser = argparse.ArgumentParser(description='Dog Robot Movement Tester')
    parser.add_argument('--ip', default='192.168.137.195', 
                       help='Robot IP address (default: 192.168.137.195)')
    parser.add_argument('--port', type=int, default=8830,
                       help='UDP port (default: 8830)')
    parser.add_argument('--mode', choices=['interactive', 'comprehensive', 'basic', 'legacy'],
                       default='interactive',
                       help='Test mode (default: interactive)')
    parser.add_argument('--duration', type=float, default=1.0,
                       help='Duration for movement tests (default: 1.0)')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        tester = MovementTester(args.ip, args.port)
        
        if args.mode == 'interactive':
            tester.interactive_test_mode()
        elif args.mode == 'comprehensive':
            results = tester.run_comprehensive_test()
            print(tester.get_test_report())
        elif args.mode == 'basic':
            tester.test_basic_movements(args.duration)
            print(tester.get_test_report())
        elif args.mode == 'legacy':
            run_predefined_sequence()
        
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        sys.exit(1)


# Legacy function for backward compatibility
def test_movements():
    """Legacy test function for backward compatibility."""
    run_predefined_sequence()


if __name__ == "__main__":
    main()