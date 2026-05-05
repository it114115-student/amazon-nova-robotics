"""
Speech executor for xiaoice Digital Human.

When a speech message is received via IoT, this executor:
1. Opens the chat UI via adb swipe (tap at 1900, 775)
2. Closes the chat UI via adb swipe (tap at 1650, 2275)
3. Waits 2 seconds
4. Opens the chat UI again via adb swipe (tap at 1900, 775)
"""

import logging
import os
import subprocess
import threading
import time

import yaml

logger = logging.getLogger(__name__)


def load_settings(settings_path: str) -> dict:
    try:
        with open(settings_path, "r", encoding="utf-8") as file:
            return yaml.safe_load(file)
    except Exception as e:
        logging.error("Failed to load settings: %s", e)
        raise


class SpeechExecutor:
    """Executes speech actions on the xiaoice Digital Human device via adb."""

    def __init__(self, settings_path: str = "settings.yaml"):
        """
        Args:
            settings_path: Path to the settings YAML file.
        """
        self.settings = load_settings(settings_path)
        self.chat_open_duration = self.settings.get("chat_open_duration", 30)
        self.adb_ip = self.settings.get("adb_ip")
        self.adb_path = self.settings.get("adb_path", r"C:\platform-tools\adb.exe")
        
        self._lock = threading.Lock()
        self._is_running = False
        
        # Connect to ADB device on initialization
        if self.adb_ip:
            self._connect_adb_device()
        else:
            logger.warning("No adb_ip specified in settings, device may not be connected")

    def _resolve_adb_executable(self) -> str:
        """Return a usable adb executable path."""
        return self.adb_path if os.path.exists(self.adb_path) else "adb"

    def _is_device_connected(self) -> bool:
        """Check whether the configured adb target appears in adb devices output."""
        if not self.adb_ip:
            return False

        cmd = [self._resolve_adb_executable(), "devices"]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                logger.error(
                    "Failed to list adb devices (rc=%d): %s",
                    result.returncode,
                    result.stderr.strip(),
                )
                return False

            for line in result.stdout.splitlines():
                if line.startswith(f"{self.adb_ip}\t") and line.rstrip().endswith("device"):
                    return True
            return False
        except Exception as e:
            logger.error("Failed checking adb connection status: %s", e)
            return False

    def _ensure_adb_connection(self) -> bool:
        """Ensure adb is connected to the configured target before sending input."""
        if not self.adb_ip:
            logger.error("adb_ip is not configured in settings.yaml")
            return False

        if self._is_device_connected():
            return True

        logger.info("ADB device %s is not connected, attempting reconnect...", self.adb_ip)
        if not self._connect_adb_device():
            return False

        if self._is_device_connected():
            logger.info("ADB device %s connected", self.adb_ip)
            return True

        logger.error("ADB device %s still not connected after reconnect attempt", self.adb_ip)
        return False

    def _connect_adb_device(self) -> bool:
        """Connect to the ADB device using the IP from settings."""
        return self._run_adb_command(
            ["connect", self.adb_ip],
            f"Connect to ADB device at {self.adb_ip}",
        )

    def _run_adb_command(self, args: list, description: str) -> bool:
        """Run an adb command and return True on success."""
        cmd = [self._resolve_adb_executable()] + args
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                logger.info("%s succeeded: %s", description, " ".join(cmd))
                return True
            else:
                logger.error(
                    "%s failed (rc=%d): %s\nstderr: %s",
                    description,
                    result.returncode,
                    " ".join(cmd),
                    result.stderr.strip(),
                )
                return False
        except subprocess.TimeoutExpired:
            logger.error("%s timed out: %s", description, " ".join(cmd))
            return False
        except FileNotFoundError:
            logger.error("adb not found at C:\\platform-tools\\adb.exe")
            return False
        except Exception as e:
            logger.error("%s error: %s", description, e)
            return False

    def open_chat(self) -> bool:
        """Open the chat UI by tapping at (1900, 775)."""
        return self._run_adb_command(
            ["shell", "input", "swipe", "1900", "775", "1900", "775", "100"],
            "Open chat",
        )

    def close_chat(self) -> bool:
        """Close the chat UI by tapping at (1650, 2275)."""
        return self._run_adb_command(
            ["shell", "input", "swipe", "1650", "2275", "1650", "2275", "100"],
            "Close chat",
        )

    def execute_speech(self, message: str) -> None:
        """
        Execute the full speech flow:
        1. Open chat
        2. Close chat
        3. Wait 2 seconds
        4. Open chat again

        This runs in a background thread so it doesn't block the MQTT listener.
        """
        thread = threading.Thread(
            target=self._execute_speech_sync,
            args=(message,),
            daemon=True,
        )
        thread.start()

    def _execute_speech_sync(self, message: str) -> None:
        """Synchronous speech execution (runs in background thread)."""
        with self._lock:
            if self._is_running:
                logger.warning(
                    "Speech already in progress, queuing will be skipped: %s",
                    message[:50],
                )
                return
            self._is_running = True

        try:
            logger.info("Speech flow started for message: %s", message[:100])

            if not self._ensure_adb_connection():
                logger.error("ADB connection unavailable, aborting speech flow")
                return

            # Step 1: Open chat (first time)
            if not self.open_chat():
                logger.error("Failed to open chat, aborting speech flow")
                return

            # Step 2: Close chat
            if not self.close_chat():
                logger.error("Failed to close chat")
                return

            # Step 3: Wait 2 seconds
            logger.info("Chat closed. Waiting 2 seconds...")
            time.sleep(2)

            # Step 4: Open chat again
            if not self.open_chat():
                logger.error("Failed to open chat on second attempt")
                return

            logger.info("Speech flow completed for message: %s", message[:100])

        except Exception as e:
            logger.error("Error during speech execution: %s", e)
        finally:
            with self._lock:
                self._is_running = False
