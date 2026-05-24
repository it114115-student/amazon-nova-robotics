#!/usr/bin/env python3
"""Unit tests for decryption, validation, and real robot dispatch utilities"""

import unittest
import base64
import json
import sys
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# Append parent directory so backend modules can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

import session_utils


class TestSessionUtils(unittest.TestCase):
    def setUp(self):
        # Match keys from session_utils (using defaults if not overridden in env)
        self.aes_key = session_utils.SESSION_AES_KEY
        self.aes_iv = session_utils.SESSION_AES_IV

    def encrypt_payload(self, data_dict: dict) -> str:
        """Helper to encrypt a python dict to match session_utils decrypt input format"""
        # Convert dictionary to JSON string
        plain_text = json.dumps(data_dict)
        
        # Apply PKCS7 padding
        padder = padding.PKCS7(algorithms.AES.block_size).padder()
        padded_bytes = padder.update(plain_text.encode('utf-8')) + padder.finalize()
        
        # Encrypt using AES-CBC
        cipher = Cipher(
            algorithms.AES(self.aes_key),
            modes.CBC(self.aes_iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        encrypted_bytes = encryptor.update(padded_bytes) + encryptor.finalize()
        
        # Encode to Base64
        base64_str = base64.b64encode(encrypted_bytes).decode('utf-8')
        return base64_str

    def test_successful_decryption(self):
        """Tests that a valid AES encrypted session key is parsed correctly"""
        excel_epoch_start = datetime(1899, 12, 30, tzinfo=ZoneInfo("Asia/Hong_Kong"))
        
        # Generate serial days for valid times (from yesterday to tomorrow)
        current_time_hk = datetime.now(ZoneInfo("Asia/Hong_Kong"))
        from_dt = current_time_hk - timedelta(days=1)
        to_dt = current_time_hk + timedelta(days=1)
        
        from_serial = (from_dt - excel_epoch_start).total_seconds() / 86400.0
        to_serial = (to_dt - excel_epoch_start).total_seconds() / 86400.0
        
        payload = {
            "robot": "all",
            "from": from_serial,
            "to": to_serial
        }
        
        encrypted_key = self.encrypt_payload(payload)
        decrypted_obj = session_utils.decrypt(encrypted_key)
        
        self.assertIsNotNone(decrypted_obj)
        self.assertEqual(decrypted_obj["robot"], "all")
        self.assertTrue(decrypted_obj["is_valid"])

    def test_expired_session_fails_validation(self):
        """Tests that a decrypted session key past its active range is marked is_valid = False"""
        excel_epoch_start = datetime(1899, 12, 30, tzinfo=ZoneInfo("Asia/Hong_Kong"))
        
        # Generate serial days for expired range (from 5 days ago to 2 days ago)
        current_time_hk = datetime.now(ZoneInfo("Asia/Hong_Kong"))
        from_dt = current_time_hk - timedelta(days=5)
        to_dt = current_time_hk - timedelta(days=2)
        
        from_serial = (from_dt - excel_epoch_start).total_seconds() / 86400.0
        to_serial = (to_dt - excel_epoch_start).total_seconds() / 86400.0
        
        payload = {
            "robot": "robot_1",
            "from": from_serial,
            "to": to_serial
        }
        
        encrypted_key = self.encrypt_payload(payload)
        decrypted_obj = session_utils.decrypt(encrypted_key)
        
        self.assertIsNotNone(decrypted_obj)
        self.assertEqual(decrypted_obj["robot"], "robot_1")
        self.assertFalse(decrypted_obj["is_valid"])

    def test_malformed_key_returns_none(self):
        """Tests that any decryption or parsing failure returns None instead of crashing"""
        # Malformed key (invalid base64)
        decrypted_obj = session_utils.decrypt("invalid_session_key_12345")
        self.assertIsNone(decrypted_obj)


if __name__ == '__main__':
    unittest.main()
