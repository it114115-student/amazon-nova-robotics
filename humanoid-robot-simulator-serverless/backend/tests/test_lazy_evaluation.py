#!/usr/bin/env python3
"""Unit tests for the lazy state evaluation logic of the Robot Simulator"""

import unittest
from unittest.mock import patch, MagicMock
import time
import sys
import os

# Append parent directory so backend modules can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lambda_function import get_clean_robot_states


class TestLazyEvaluation(unittest.TestCase):
    def setUp(self):
        # Set up a sample robots state
        self.robots = {
            'robot_1': {
                'robot_id': 'robot_1',
                'current_action': 'wave',
                'action_start_time': 1000.0,
                'action_duration': 3.5,
                'is_animating': True
            },
            'robot_2': {
                'robot_id': 'robot_2',
                'current_action': 'bow',
                'action_start_time': 1000.0,
                'action_duration': 4.0,
                'is_animating': True
            },
            'robot_3': {
                'robot_id': 'robot_3',
                'current_action': 'idle',
                'action_start_time': 0.0,
                'action_duration': 0.0,
                'is_animating': False
            }
        }

    @patch('lambda_function.save_session_robots')
    @patch('time.time')
    def test_active_actions_preserved(self, mock_time, mock_save):
        """Tests that actions that are still within their duration are preserved"""
        # Set current time to 1002.0 (only 2 seconds since start_time 1000.0)
        mock_time.return_value = 1002.0
        
        cleaned = get_clean_robot_states('test_session', self.robots)
        
        # Verify robot_1 and robot_2 are still animating and have active actions
        self.assertTrue(cleaned['robot_1']['is_animating'])
        self.assertEqual(cleaned['robot_1']['current_action'], 'wave')
        self.assertTrue(cleaned['robot_2']['is_animating'])
        self.assertEqual(cleaned['robot_2']['current_action'], 'bow')
        
        # save_session_robots should NOT be called since no state changed
        mock_save.assert_not_called()

    @patch('lambda_function.save_session_robots')
    @patch('time.time')
    def test_expired_actions_cleaned(self, mock_time, mock_save):
        """Tests that actions that have exceeded their duration are expired back to idle"""
        # Set current time to 1005.0 (5 seconds since start_time 1000.0 - both wave [3.5s] and bow [4.0s] expired)
        mock_time.return_value = 1005.0
        
        cleaned = get_clean_robot_states('test_session', self.robots)
        
        # Verify robot_1 and robot_2 have returned to idle
        self.assertFalse(cleaned['robot_1']['is_animating'])
        self.assertEqual(cleaned['robot_1']['current_action'], 'idle')
        self.assertFalse(cleaned['robot_2']['is_animating'])
        self.assertEqual(cleaned['robot_2']['current_action'], 'idle')
        
        # save_session_robots should be called to persist the cleaned state
        mock_save.assert_called_once_with('test_session', self.robots)

    @patch('lambda_function.save_session_robots')
    @patch('time.time')
    def test_partial_expiration(self, mock_time, mock_save):
        """Tests that some actions expire while others remain active based on durations"""
        # Set current time to 1003.8 (3.8 seconds since start_time 1000.0)
        # wave (duration 3.5) should be expired
        # bow (duration 4.0) should remain active
        mock_time.return_value = 1003.8
        
        cleaned = get_clean_robot_states('test_session', self.robots)
        
        # robot_1 (wave) should expire
        self.assertFalse(cleaned['robot_1']['is_animating'])
        self.assertEqual(cleaned['robot_1']['current_action'], 'idle')
        
        # robot_2 (bow) should remain active
        self.assertTrue(cleaned['robot_2']['is_animating'])
        self.assertEqual(cleaned['robot_2']['current_action'], 'bow')
        
        # save_session_robots should be called since state changed
        mock_save.assert_called_once_with('test_session', self.robots)


if __name__ == '__main__':
    unittest.main()
