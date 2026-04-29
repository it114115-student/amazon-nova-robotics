"""
Speech executor for xiaoice Digital Human.

When a speech message is received via IoT, this executor:
1. Opens the chat UI via adb swipe (tap at 1900, 775)
2. Closes the chat UI via adb swipe (tap at 1650, 2275)
3. Waits 2 seconds
4. Opens the chat UI again via adb swipe (tap at 1900, 775)
"""

import logging
import subprocess
import threading
import time

logger = logging.getLogger(__name__)


class SpeechExecutor:
    """Executes speech actions on the xiaoice Digital Human device via adb."""

    def __init__(self, chat_open_duration: int = 30):
        """
        Args:
            chat_open_duration: Seconds to keep the chat open before closing.
        """
        self.chat_open_duration = chat_open_duration
        self._lock = threading.Lock()
        self._is_running = False

    def _run_adb_command(self, args: list, description: str) -> bool:
        """Run an adb command and return True on success."""
        cmd = [r"C:\platform-tools\adb.exe"] + args
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

    def stop_speech(self) -> None:
        """Immediately close the chat (used for stop_speech commands)."""
        logger.info("Stop speech requested, closing chat immediately")
        self.close_chat()
