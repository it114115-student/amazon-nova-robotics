/**
 * SpeechPlayer - Per-robot concurrent audio player for the simulator.
 *
 * Manages one Audio instance per robot so multiple robots can speak
 * simultaneously.  If a new speech arrives for the SAME robot while
 * it is still speaking, the old one is interrupted and the new one
 * starts.  Speech for DIFFERENT robots plays concurrently.
 *
 * Usage:
 *   window.speechPlayer.play(robotId, url, text);
 *   window.speechPlayer.stop(robotId);   // stop one robot
 *   window.speechPlayer.stopAll();       // stop every robot
 */
class SpeechPlayer {
    constructor() {
        if (SpeechPlayer._instance) {
            return SpeechPlayer._instance;
        }
        SpeechPlayer._instance = this;

        /** @type {Map<string, HTMLAudioElement>} robotId → Audio */
        this._channels = new Map();

        /** @type {boolean} */
        this._deviceAvailable = this._checkAudioDevice();

        /** @type {boolean} Whether speech playback is enabled (controlled by UI toggle) */
        this.enabled = true;

        // Unlock audio context on first user interaction (mobile / autoplay policy)
        const unlock = () => {
            document.removeEventListener('click', unlock);
            document.removeEventListener('touchstart', unlock);
            document.removeEventListener('keydown', unlock);
        };
        document.addEventListener('click', unlock, { once: false });
        document.addEventListener('touchstart', unlock, { once: false });
        document.addEventListener('keydown', unlock, { once: false });

        console.log(`🔊 SpeechPlayer initialized (per-robot) — audio device: ${this._deviceAvailable}`);
    }

    /* ------------------------------------------------------------------ */
    /*  Public API                                                         */
    /* ------------------------------------------------------------------ */

    /**
     * Play speech audio for a specific robot.
     * If the same robot is already speaking, the old audio is stopped first.
     * Different robots play concurrently.
     *
     * @param {string} robotId  Robot identifier (e.g. "robot_1").
     * @param {string} url      Presigned S3 URL for the audio file.
     * @param {string} [text]   Optional display text (for logging / UI).
     */
    play(robotId, url, text) {
        if (!url) {
            console.warn('🔊 SpeechPlayer.play() called with empty URL');
            return;
        }

        if (!this.enabled) {
            console.log(`🔇 Speech disabled, ignoring: [${robotId}] "${text || ''}"`);
            return;
        }

        if (!this._deviceAvailable) {
            console.warn('🔊 No audio output device detected — speech will not play');
            this._showNotification('No audio device found', 'warning');
            return;
        }

        // Stop any current speech for THIS robot only
        this.stop(robotId);

        console.log(`🔊 [${robotId}] Playing: "${text || '(no text)'}" — ${url.substring(0, 80)}…`);

        const audio = new Audio();
        audio.crossOrigin = 'anonymous';
        audio.preload = 'auto';
        audio.volume = 1.0;

        // Named functions for easy removal
        const onEnded = () => {
            console.log(`🔊 [${robotId}] Speech finished`);
            this._cleanupChannel(robotId, audio, onEnded, onError);
        };

        const onLoadedMetadata = () => {
            console.log(`🔊 [${robotId}] Metadata loaded - Duration: ${audio.duration.toFixed(2)}s`);
        };

        const onError = (e) => {
            // Only log if not already cleaned up
            if (audio.src) {
                const err = audio.error;
                let msg = 'Unknown error';
                if (err) {
                    switch (err.code) {
                        case 1: msg = 'Aborted'; break;
                        case 2: msg = 'Network error'; break;
                        case 3: msg = 'Decoding error'; break;
                        case 4: msg = 'Source not supported'; break;
                    }
                }
                console.error(`🔊 [${robotId}] Speech error (${msg}):`, e);
                this._showNotification(`Speech failed for ${robotId}: ${msg}`, 'error');
            }
            this._cleanupChannel(robotId, audio, onEnded, onError, onLoadedMetadata);
        };

        audio.addEventListener('ended', onEnded);
        audio.addEventListener('error', onError);
        audio.addEventListener('loadedmetadata', onLoadedMetadata);

        this._channels.set(robotId, audio);
        audio.src = url;

        audio.play().then(() => {
            console.log(`🔊 [${robotId}] Playback started`);
            if (text) {
                this._showNotification(`🗣️ ${robotId}: "${text}"`, 'info');
            }
        }).catch((err) => {
            console.warn(`🔊 [${robotId}] Autoplay blocked:`, err.message);
            const retryPlay = () => {
                if (this._channels.get(robotId) === audio) {
                    audio.play().catch(() => { });
                }
                document.removeEventListener('click', retryPlay);
            };
            document.addEventListener('click', retryPlay, { once: true });
            this._showNotification('Click anywhere to enable speech audio', 'warning');
        });
    }

    /**
     * Stop speech for a specific robot.
     * @param {string} robotId
     */
    stop(robotId) {
        const audio = this._channels.get(robotId);
        if (audio) {
            try {
                audio.pause();
                // We don't have the original listeners here, so we just clear src
                // If it was called from stop(), it's likely a manual override
                audio.src = '';
                audio.load(); // Force release of resources
            } catch (_) { /* ignore */ }
            this._channels.delete(robotId);
        }
    }

    /**
     * Stop all robots' speech.
     */
    stopAll() {
        for (const robotId of [...this._channels.keys()]) {
            this.stop(robotId);
        }
    }

    /**
     * Check if a specific robot is currently speaking.
     * @param {string} robotId
     * @returns {boolean}
     */
    isPlaying(robotId) {
        const audio = this._channels.get(robotId);
        return audio !== undefined && !audio.paused && !audio.ended;
    }

    /**
     * @returns {string[]} List of robot IDs currently speaking.
     */
    get activeSpeakers() {
        return [...this._channels.keys()].filter(id => this.isPlaying(id));
    }

    /* ------------------------------------------------------------------ */
    /*  Internal helpers                                                    */
    /* ------------------------------------------------------------------ */

    /**
     * Proper cleanup of an audio channel.
     */
    _cleanupChannel(robotId, audio, onEnded, onError, onLoadedMetadata) {
        audio.removeEventListener('ended', onEnded);
        audio.removeEventListener('error', onError);
        if (onLoadedMetadata) {
            audio.removeEventListener('loadedmetadata', onLoadedMetadata);
        }
        
        if (this._channels.get(robotId) === audio) {
            this._channels.delete(robotId);
        }
        
        try {
            audio.pause();
            audio.src = '';
            audio.load();
        } catch (_) { }
    }

    _checkAudioDevice() {
        if (typeof navigator !== 'undefined' && navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {
            navigator.mediaDevices.enumerateDevices().then((devices) => {
                const hasOutput = devices.some((d) => d.kind === 'audiooutput');
                if (!hasOutput) {
                    console.warn('🔊 No audio output device detected');
                    this._deviceAvailable = false;
                }
            }).catch(() => { });
        }
        return typeof Audio !== 'undefined';
    }

    _showNotification(message, type) {
        if (window.simulator && typeof window.simulator.showNotification === 'function') {
            window.simulator.showNotification(message, type);
        }
    }
}

// Export singleton instance
window.speechPlayer = new SpeechPlayer();
