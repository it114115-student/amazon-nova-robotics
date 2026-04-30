"""
Singleton speech audio player for the humanoid robot client.

Receives presigned S3 URLs (Amazon Polly audio) and plays them on the
Raspberry Pi's audio output.

Rules:
  1. Only one playback process/thread runs at any time.
  2. If new speech arrives while old speech is playing, the old one is
     stopped immediately and the new one starts.
  3. Gracefully handles missing audio device.

Playback strategy (in priority order):
  - mpv   (lightweight, streams URLs directly, no download needed)
  - ffplay (part of ffmpeg, also streams URLs)
  - pygame.mixer (requires download first, fallback)
  - aplay  (requires download + wav conversion, last resort)

On Raspberry Pi, install one of: sudo apt install mpv  OR  sudo apt install ffmpeg
"""

import logging
import os
import shutil
import subprocess
import tempfile
import threading
from typing import Optional

import requests

logger = logging.getLogger(__name__)


class SpeechPlayer:
    """Singleton audio player for robot speech."""

    _instance: Optional["SpeechPlayer"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "SpeechPlayer":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True

        self._play_lock = threading.Lock()
        self._current_process: Optional[subprocess.Popen] = None
        self._current_thread: Optional[threading.Thread] = None

        # Detect available player
        self._player = self._detect_player()
        logger.info("SpeechPlayer initialized — player: %s", self._player or "NONE")

    # ------------------------------------------------------------------
    #  Public API
    # ------------------------------------------------------------------

    def play(self, url: str, text: str = "") -> None:
        """Play speech audio from a URL. Interrupts any current playback."""
        if not url:
            logger.warning("SpeechPlayer.play() called with empty URL")
            return

        if not self._player:
            logger.error(
                "No audio player available. Install mpv or ffmpeg on this device."
            )
            return

        # Stop current playback
        self.stop()

        logger.info('Playing speech: "%s" — %s', text[:80] if text else "(no text)", url[:100])

        thread = threading.Thread(
            target=self._play_thread, args=(url, text), daemon=True
        )
        self._current_thread = thread
        thread.start()

    def stop(self) -> None:
        """Stop any currently playing speech immediately."""
        with self._play_lock:
            if self._current_process and self._current_process.poll() is None:
                logger.info("Stopping current speech playback (pid=%d)", self._current_process.pid)
                try:
                    self._current_process.terminate()
                    self._current_process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self._current_process.kill()
                except Exception as e:
                    logger.warning("Error stopping playback: %s", e)
                finally:
                    self._current_process = None

    @property
    def is_playing(self) -> bool:
        with self._play_lock:
            return (
                self._current_process is not None
                and self._current_process.poll() is None
            )

    # ------------------------------------------------------------------
    #  Internal
    # ------------------------------------------------------------------

    def _detect_player(self) -> Optional[str]:
        """Detect which audio player is available on this system."""
        for cmd in ("mpv", "ffplay", "aplay"):
            if shutil.which(cmd):
                return cmd
        return None

    def _play_thread(self, url: str, text: str) -> None:
        """Background thread that performs the actual playback."""
        try:
            if self._player == "mpv":
                self._play_with_mpv(url)
            elif self._player == "ffplay":
                self._play_with_ffplay(url)
            elif self._player == "aplay":
                self._play_with_download(url)
            else:
                logger.error("No player available")
        except Exception as e:
            logger.error("Speech playback error: %s", e)
        finally:
            with self._play_lock:
                self._current_process = None

    def _play_with_mpv(self, url: str) -> None:
        """Play using mpv (streams directly, no download)."""
        cmd = [
            "mpv",
            "--no-video",
            "--really-quiet",
            "--no-terminal",
            url,
        ]
        with self._play_lock:
            self._current_process = subprocess.Popen(
                cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        self._current_process.wait()

    def _play_with_ffplay(self, url: str) -> None:
        """Play using ffplay (streams directly, no download)."""
        cmd = [
            "ffplay",
            "-nodisp",
            "-autoexit",
            "-loglevel", "quiet",
            url,
        ]
        with self._play_lock:
            self._current_process = subprocess.Popen(
                cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        self._current_process.wait()

    def _play_with_download(self, url: str) -> None:
        """Download the file first, then play with aplay (mp3→wav via ffmpeg or direct)."""
        tmp_path = None
        wav_path = None
        try:
            # Download
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()

            tmp_fd, tmp_path = tempfile.mkstemp(suffix=".mp3")
            with os.fdopen(tmp_fd, "wb") as f:
                f.write(resp.content)

            logger.info("Downloaded speech audio (%d bytes)", len(resp.content))

            # Convert mp3 → wav if ffmpeg is available
            if shutil.which("ffmpeg"):
                wav_path = tmp_path.replace(".mp3", ".wav")
                subprocess.run(
                    ["ffmpeg", "-y", "-i", tmp_path, "-ar", "44100", "-ac", "1", wav_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=30,
                )
                play_file = wav_path
            else:
                # Try playing mp3 directly (may not work with aplay)
                play_file = tmp_path

            cmd = ["aplay", play_file]
            with self._play_lock:
                self._current_process = subprocess.Popen(
                    cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
            self._current_process.wait()

        except Exception as e:
            logger.error("Download+play failed: %s", e)
        finally:
            for path in (tmp_path, wav_path):
                if path and os.path.exists(path):
                    try:
                        os.unlink(path)
                    except OSError:
                        pass
