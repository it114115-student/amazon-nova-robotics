#!/usr/bin/env python3
"""Unit tests for the monolithic REST & WebSocket AWS Lambda handler"""

import unittest
from unittest.mock import patch, MagicMock
import json
import sys
import os

# Append parent directory so backend modules can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import lambda_function


class TestLambdaHandler(unittest.TestCase):
    @patch('lambda_function.sessions_table')
    def test_health_endpoint(self, mock_sess_table):
        """Tests the GET /health REST API path"""
        event = {
            "rawPath": "/health",
            "requestContext": {
                "http": {
                    "method": "GET"
                }
            }
        }
        response = lambda_function.lambda_handler(event, None)
        
        self.assertEqual(response["statusCode"], 200)
        body = json.loads(response["body"])
        self.assertEqual(body["status"], "healthy")
        self.assertEqual(body["service"], "robot-simulator-serverless")

    @patch('lambda_function.get_session_robots')
    def test_api_status_no_session(self, mock_get_robots):
        """Tests the GET /api/status route when no session_key is provided"""
        event = {
            "rawPath": "/api/status",
            "requestContext": {
                "http": {
                    "method": "GET"
                }
            }
        }
        response = lambda_function.lambda_handler(event, None)
        
        self.assertEqual(response["statusCode"], 200)
        body = json.loads(response["body"])
        self.assertEqual(body["server"], "running")
        self.assertTrue(body["session_required"])
        mock_get_robots.assert_not_called()

    @patch('lambda_function.get_session_robots')
    def test_api_status_with_session(self, mock_get_robots):
        """Tests the GET /api/status route when session_key is provided"""
        mock_get_robots.return_value = {
            "robot_1": {"is_animating": True, "current_action": "wave"},
            "robot_2": {"is_animating": False, "current_action": "idle"}
        }
        
        event = {
            "rawPath": "/api/status",
            "queryStringParameters": {
                "session_key": "test_session_123"
            },
            "requestContext": {
                "http": {
                    "method": "GET"
                }
            }
        }
        response = lambda_function.lambda_handler(event, None)
        
        self.assertEqual(response["statusCode"], 200)
        body = json.loads(response["body"])
        self.assertEqual(body["server"], "running")
        self.assertEqual(body["robots_count"], 2)
        self.assertEqual(body["animating_robots"], ["robot_1"])
        mock_get_robots.assert_called_once_with("test_session_123")

    @patch('lambda_function.connections_table')
    def test_websocket_connect(self, mock_conn_table):
        """Tests the WebSocket $connect route"""
        event = {
            "requestContext": {
                "connectionId": "cid_9999",
                "routeKey": "$connect"
            },
            "queryStringParameters": {
                "session_key": "test_ws_session"
            }
        }
        response = lambda_function.lambda_handler(event, None)
        
        self.assertEqual(response["statusCode"], 200)
        # Verify connection registration in connections database
        mock_conn_table.put_item.assert_called_once()

    @patch('lambda_function.connections_table')
    def test_websocket_disconnect(self, mock_conn_table):
        """Tests the WebSocket $disconnect route"""
        event = {
            "requestContext": {
                "connectionId": "cid_9999",
                "routeKey": "$disconnect"
            }
        }
        response = lambda_function.lambda_handler(event, None)
        
        self.assertEqual(response["statusCode"], 200)
        # Verify connection removal from connections database
        mock_conn_table.delete_item.assert_called_once_with(Key={'connection_id': 'cid_9999'})

    @patch('lambda_function.post_to_single_connection')
    @patch('lambda_function.get_session_robots')
    def test_websocket_join_session(self, mock_get_robots, mock_post_single):
        """Tests the WebSocket $default route with join_session custom action"""
        mock_robots_state = {"robot_1": {"robot_id": "robot_1"}}
        mock_get_robots.return_value = mock_robots_state
        
        event = {
            "requestContext": {
                "connectionId": "cid_1111",
                "routeKey": "$default",
                "domainName": "abc.execute-api.us-east-1.amazonaws.com",
                "stage": "test"
            },
            "body": json.dumps({
                "action": "join_session",
                "session_key": "session_ws_456"
            })
        }
        response = lambda_function.lambda_handler(event, None)
        
        self.assertEqual(response["statusCode"], 200)
        # Verify robot states are retrieved and single connection callback was triggered
        mock_get_robots.assert_called_once_with("session_ws_456")
        mock_post_single.assert_called_once_with(event, "cid_1111", {
            "type": "robot_states",
            "data": mock_robots_state
        })

    @patch('lambda_function.post_to_connections')
    def test_api_digital_human_speak_success(self, mock_post_connections):
        """Tests the POST /api/digital-human/speak REST API endpoint with a valid message"""
        event = {
            "rawPath": "/api/digital-human/speak",
            "requestContext": {
                "http": {
                    "method": "POST"
                }
            },
            "queryStringParameters": {
                "session_key": "test_dh_session"
            },
            "body": json.dumps({
                "message": "Hello, this is a test of the digital human speaking!",
                "audio_url": "https://s3.amazonaws.com/test-bucket/audio.mp3"
            })
        }
        response = lambda_function.lambda_handler(event, None)
        
        self.assertEqual(response["statusCode"], 200)
        body = json.loads(response["body"])
        self.assertEqual(body["success"], True)
        self.assertEqual(body["message"], "Digital human speech broadcasted")
        
        mock_post_connections.assert_called_once_with(
            event,
            "test_dh_session",
            {
                "type": "digital_human_speech",
                "data": {
                    "message": "Hello, this is a test of the digital human speaking!",
                    "audio_url": "https://s3.amazonaws.com/test-bucket/audio.mp3",
                    "session_key": "test_dh_session"
                }
            }
        )

    @patch('lambda_function.post_to_connections')
    def test_api_digital_human_speak_missing_message(self, mock_post_connections):
        """Tests the POST /api/digital-human/speak route when no message is provided"""
        event = {
            "rawPath": "/api/digital-human/speak",
            "requestContext": {
                "http": {
                    "method": "POST"
                }
            },
            "queryStringParameters": {
                "session_key": "test_dh_session"
            },
            "body": json.dumps({})
        }
        response = lambda_function.lambda_handler(event, None)
        
        self.assertEqual(response["statusCode"], 400)
        body = json.loads(response["body"])
        self.assertEqual(body["success"], False)
        self.assertEqual(body["error"], "message is required")
        mock_post_connections.assert_not_called()


if __name__ == '__main__':
    unittest.main()
