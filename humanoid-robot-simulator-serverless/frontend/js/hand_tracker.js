/**
 * Hand Tracker for 3D Camera Control
 * Uses MediaPipe Hands to detect gestures and send them via WebSocket
 */

class DomainExpansionGame {
    constructor() {
        this.stableDomain = null;
        this.domainColors = {};
        this.displayNames = {};
    }
    initVFX() {}
    update() { return null; }
    drawVFX() {}
}

class HandTracker {
    constructor() {
        this.video = document.getElementById('webcam');
        this.canvas = document.getElementById('output-canvas');
        this.ctx = this.canvas.getContext('2d');
        
        this.vfxCanvas = document.getElementById('vfx-canvas');
        this.domainGame = new DomainExpansionGame();
        
        this.sessionKey = window.sessionKey;
        this.socket = null;
        
        this.hands = new Hands({
            locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`
        });
        
        this.hands.setOptions({
            maxNumHands: 2,
            modelComplexity: 1,
            minDetectionConfidence: 0.5,
            minTrackingConfidence: 0.5
        });
        
        this.hands.onResults(this.onResults.bind(this));
        
        this.camera = new Camera(this.video, {
            onFrame: async () => {
                // Ensure canvas matches video display size
                if (this.canvas.width !== this.video.videoWidth || this.canvas.height !== this.video.videoHeight) {
                    this.canvas.width = this.video.videoWidth;
                    this.canvas.height = this.video.videoHeight;
                    this.vfxCanvas.width = this.video.videoWidth;
                    this.vfxCanvas.height = this.video.videoHeight;
                    this.domainGame.initVFX(this.vfxCanvas);
                }
                await this.hands.send({image: this.video});
            },
            width: 1280,
            height: 720
        });
        
        this.prevHands = [];
        this.lastEmitTime = 0;
        
        // --- 1. Mode Control ---
        this.modeSelect = document.getElementById('operation-mode');
        this.robotSelect = document.getElementById('robot-select');
        this.modeDisplay = document.getElementById('mode-display');
        this.domainDisplay = document.getElementById('domain-display');
        this.cameraSettings = document.getElementById('camera-settings');
        this.cooldownSettings = document.getElementById('cooldown-settings');
        this.instructionsPanel = document.getElementById('instructions-panel');
        
        this.operationMode = this.modeSelect ? this.modeSelect.value : 'camera';
        if (this.modeSelect) {
            this.modeSelect.addEventListener('change', () => {
                this.operationMode = this.modeSelect.value;
                this.updateUIMode();
            });
        }

        // --- 2. Cooldown Sliders ---
        this.simSlider = document.getElementById('sim-cooldown-slider');
        this.simLabel = document.getElementById('sim-cooldown-val');
        this.realSlider = document.getElementById('real-cooldown-slider');
        this.realLabel = document.getElementById('real-cooldown-val');

        this.lastSimActionTime = 0;
        this.lastSimDomain = null;
        this.lastRealActionTime = 0;
        this.lastRealDomain = null;

        if (this.simSlider) {
            this.simSlider.addEventListener('input', () => {
                this.simCooldownMs = parseInt(this.simSlider.value) * 1000;
                if (this.simLabel) this.simLabel.textContent = this.simSlider.value;
            });
        }

        if (this.realSlider) {
            this.realSlider.addEventListener('input', () => {
                this.realCooldownMs = parseInt(this.realSlider.value) * 1000;
                if (this.realLabel) this.realLabel.textContent = this.realSlider.value;
            });
        }

        // --- 3. Sensitivity Sliders ---
        this.rotateSens = document.getElementById('rotate-sensitivity');
        this.rotateLabel = document.getElementById('rotate-val');
        this.zoomSens = document.getElementById('zoom-sensitivity');
        this.zoomLabel = document.getElementById('zoom-val');
        this.panSens = document.getElementById('pan-sensitivity');
        this.panLabel = document.getElementById('pan-val');

        if (this.rotateSens) this.rotateSens.addEventListener('input', () => { if (this.rotateLabel) this.rotateLabel.textContent = this.rotateSens.value; });
        if (this.zoomSens) this.zoomSens.addEventListener('input', () => { if (this.zoomLabel) this.zoomLabel.textContent = this.zoomSens.value; });
        if (this.panSens) this.panSens.addEventListener('input', () => { if (this.panLabel) this.panLabel.textContent = this.panSens.value; });

        // --- 4. System Controls ---
        this.resetCameraBtn = document.getElementById('reset-camera-btn');
        this.intervalSlider = document.getElementById('emit-interval');
        this.intervalLabel = document.getElementById('interval-value');

        if (this.intervalSlider) {
            this.intervalSlider.addEventListener('input', () => {
                this.emitInterval = parseInt(this.intervalSlider.value);
                const fps = Math.round(1000 / this.emitInterval);
                if (this.intervalLabel) this.intervalLabel.textContent = `${this.emitInterval}ms (${fps} updates/s)`;
            });
        }

        // --- 5. VFX Elements ---
        this.mainContainer = document.getElementById('main-container');
        this.atmosphereOverlay = document.getElementById('atmosphere-overlay');
        this.lastVFXDomain = null;

        if (this.resetCameraBtn) {
            this.resetCameraBtn.addEventListener('click', () => {
                console.log(`📷 Requesting Camera Reset for session: ${this.sessionKey}`);
                this.emitControl('reset', { force: true });
            });
        }

        // --- 5. Initial Sync ---
        this.emitInterval = parseInt(this.intervalSlider.value);
        this.simCooldownMs = parseInt(this.simSlider.value) * 1000;
        this.realCooldownMs = parseInt(this.realSlider.value) * 1000;
        this.videoBaseUrl = window.videoBucketUrl || '';
        this.resetTimer = null;

        this.init();
    }
    
    updateUIMode() {
        if (this.operationMode === 'camera') {
            this.modeDisplay.textContent = 'Control the 3D scene with gestures';
            this.cameraSettings.style.display = 'block';
            this.cooldownSettings.style.display = 'none';
            this.instructionsPanel.innerHTML = `
                <strong>1 Hand:</strong> Move to rotate. <br>
                <strong>2 Hands:</strong> Apart/Together to zoom. <br>
                Move same direction to pan.
            `;
            this.domainDisplay.textContent = '';
        } else {
            this.modeDisplay.textContent = 'Strike a hand sign to expand your domain!';
            this.cameraSettings.style.display = 'none';
            this.cooldownSettings.style.display = 'block';
            this.instructionsPanel.innerHTML = `
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 0.85em;">
                    <div>
                        <strong>— Domains —</strong><br>
                        • 五條悟: 無量空處 (1H)<br>
                        • 兩面宿儺: 伏魔御廚子 (2H)<br>
                        • 真人: 自閉圓頓裹 (2H)<br>
                        • 乙骨憂太: 真贋相愛 (2H Wide)<br>
                        • 秤金次: 坐殺博徒 (2H Stack)<br>
                        • 伏黑惠: 嵌合暗翳庭園 (2H Fists)<br>
                        • 直哉: 時胞月宮殿 (2H L-sign)<br>
                        • 虎杖: 名称不明 (2H Point)
                    </div>
                    <div>
                        <strong>— Techniques —</strong><br>
                        • 蒼 (Blue): Index Point (1H)<br>
                        • 赫 (Red): Open Palm (1H)<br>
                        • 茈 (Purple): Blue + Red (2H)
                    </div>
                </div>
            `;
        }
    }

    init() {
        console.log('🚀 Initializing HandTracker...');
        this.connectSocket();
        this.camera.start();
        this.updateUIMode();
        
        const trackingStatus = document.getElementById('tracking-status');
        const trackingDot = document.getElementById('tracking-dot');
        trackingStatus.textContent = 'Active';
        trackingDot.classList.add('active');
    }
    
    connectSocket() {
        const wsStatus = document.getElementById('ws-status');
        const wsDot = document.getElementById('ws-dot');

        const urlParams = new URLSearchParams(window.location.search);
        let wsUrl = '';
        if (urlParams.has('ws_url')) {
            wsUrl = urlParams.get('ws_url');
        } else {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            wsUrl = `${protocol}//${window.location.host}/ws?session_key=${this.sessionKey}`;
        }

        console.log(`🔌 Connecting to WebSocket session: ${this.sessionKey} at ${wsUrl}`);
        this.socket = new WebSocket(wsUrl);

        this.socket.onopen = () => {
            console.log('✅ Connected to WebSocket');
            if (wsStatus) wsStatus.textContent = 'Connected';
            if (wsDot) wsDot.classList.add('active');
            
            this.socket.send(JSON.stringify({
                action: 'join_session',
                session_key: this.sessionKey
            }));
        };

        this.socket.onclose = () => {
            console.log('❌ Disconnected from WebSocket');
            if (wsStatus) wsStatus.textContent = 'Disconnected';
            if (wsDot) wsDot.classList.remove('active');
        };

        this.socket.onerror = (error) => {
            console.error('❌ WebSocket error:', error);
        };
    }
    
    onResults(results) {
        try {
            // Draw visual feedback
            this.ctx.save();
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
            
            let stableDomain = null;

            if (results.multiHandLandmarks) {
                // Determine skeleton color based on domain
                let skeletonColor = '#00FF00'; // Default green
                const currentDomain = this.domainGame.stableDomain;
                if (currentDomain && this.domainGame.domainColors[currentDomain]) {
                    skeletonColor = this.domainGame.domainColors[currentDomain];
                }

                for (const landmarks of results.multiHandLandmarks) {
                    if (typeof drawConnectors === 'function' && typeof HAND_CONNECTIONS !== 'undefined') {
                        drawConnectors(this.ctx, landmarks, HAND_CONNECTIONS, {color: skeletonColor, lineWidth: 5});
                    }
                    if (typeof drawLandmarks === 'function') {
                        drawLandmarks(this.ctx, landmarks, {color: '#FF0000', lineWidth: 2});
                    }
                }
                
                if (this.operationMode === 'camera') {
                    this.processGestures(results.multiHandLandmarks);
                    stableDomain = this.domainGame.update([]); // Update with empty to clear history
                } else {
                    stableDomain = this.domainGame.update(results.multiHandLandmarks);
                }
            } else {
                stableDomain = this.domainGame.update([]); // No hands: clear history
            }

            // ALWAYS execute these logic blocks to ensure UI and Canvas are reset properly
            if (this.operationMode === 'domain') {
                this.processDomainExpansion(stableDomain);
                this.domainGame.drawVFX(this.vfxCanvas, stableDomain, results.multiHandLandmarks);
            } else {
                // Camera mode: ensure everything is cleared/reset
                this.processDomainExpansion(null); 
                this.domainGame.drawVFX(this.vfxCanvas, null, []);
            }

            this.ctx.restore();
        } catch (err) {
            console.error('❌ Error in hand tracking loop:', err);
            this.ctx.restore();
        }
    }

    hexToRgba(hex, opacity) {
        let r = 0, g = 0, b = 0;
        if (hex.length === 4) {
            r = parseInt(hex[1] + hex[1], 16);
            g = parseInt(hex[2] + hex[2], 16);
            b = parseInt(hex[3] + hex[3], 16);
        } else if (hex.length === 7) {
            r = parseInt(hex.substring(1, 3), 16);
            g = parseInt(hex.substring(3, 5), 16);
            b = parseInt(hex.substring(5, 7), 16);
        }
        return `rgba(${r}, ${g}, ${b}, ${opacity})`;
    }

    processDomainExpansion(stableDomain) {
        if (stableDomain) {
            if (this.resetTimer) {
                clearTimeout(this.resetTimer);
                this.resetTimer = null;
            }

            const now = Date.now();
            const displayName = this.domainGame.displayNames[stableDomain] || stableDomain;
            const domainColor = this.domainGame.domainColors[stableDomain];
            const actionMap = {
                "Unlimited Void": "domain_unlimited_void",
                "Malevolent Shrine": "domain_malevolent_shrine",
                "Self-Embodiment of Perfection": "domain_self_embodiment",
                "Authentic Mutual Love": "domain_authentic_love",
                "Idle Death Gamble": "domain_idle_death_gamble",
                "Yuji Itadori": "domain_yuji_itadori",
                "Chimera Shadow Garden": "domain_chimera_shadow_garden",
                "Time Cell Moon Palace": "domain_time_cell_moon_palace",
                "Lapse Blue": "lapse_blue",
                "Reversal Red": "reversal_red",
                "Hollow Purple": "hollow_purple"
            };
            const action = actionMap[stableDomain];

            // 1. UI & VFX Update (ALWAYS INSTANT)
            this.domainDisplay.textContent = displayName;
            if (domainColor) this.domainDisplay.style.color = domainColor;
            this.domainDisplay.style.opacity = "1.0";

            // 2. TRIGGER SCREEN SHAKE & ATMOSPHERE (ONLY ON FIRST STABLE DETECTION)
            if (this.lastVFXDomain !== stableDomain) {
                this.lastVFXDomain = stableDomain;
                
                // Add shake class
                if (this.mainContainer) {
                    this.mainContainer.classList.remove('shake');
                    void this.mainContainer.offsetWidth; // Force reflow
                    this.mainContainer.classList.add('shake');
                    setTimeout(() => this.mainContainer.classList.remove('shake'), 500);
                }

                // Set atmospheric tint - Solid color instead of radial gradient to fix blur bug
                if (this.atmosphereOverlay && domainColor) {
                    this.atmosphereOverlay.style.background = this.hexToRgba(domainColor, 0.15);
                }
            }

            // 3. SIMULATION TRIGGER (STRICT COOLDOWN)
            if (now - this.lastSimActionTime >= this.simCooldownMs) {
                if (action && this.socket && this.socket.readyState === WebSocket.OPEN) {
                    this.lastSimActionTime = now;
                    this.lastSimDomain = stableDomain;
                    const targetRobot = this.robotSelect.value;
                    console.log(`🎮 Sim Trigger (${this.simCooldownMs/1000}s) for ${targetRobot}: ${displayName}`);
                    
                    this.socket.send(JSON.stringify({ 
                        action: 'robot_action',
                        session_key: this.sessionKey, 
                        robot_id: targetRobot, 
                        action_name: action 
                    }));

                    // Update Video
                    const videoMap = {
                        "Unlimited Void": "domain_unlimited_void.mp4",
                        "Malevolent Shrine": "domain_malevolent_shrine.mp4",
                        "Self-Embodiment of Perfection": "domain_self_embodiment.mp4",
                        "Authentic Mutual Love": "domain_authentic_love.mp4",
                        "Idle Death Gamble": "domain_idle_death_gamble.mp4",
                        "Yuji Itadori": "domain_yuji_itadori.mp4",
                        "Chimera Shadow Garden": "domain_chimera_shadow_garden.mp4",
                        "Time Cell Moon Palace": "domain_time_cell_moon_palace.mp4",
                        "Lapse Blue": "technique_lapse_blue.mp4",
                        "Reversal Red": "technique_reversal_red.mp4",
                        "Hollow Purple": "technique_hollow_purple.mp4"
                    };
                    const videoFile = videoMap[stableDomain];
                    if (videoFile) {
                        this.socket.send(JSON.stringify({
                            action: 'change_video_source',
                            session_key: this.sessionKey,
                            video_src: `${this.videoBaseUrl}${videoFile}`
                        }));
                    }
                }
            }

            // 4. REAL ROBOT TRIGGER (STRICT COOLDOWN)
            if (now - this.lastRealActionTime >= this.realCooldownMs) {
                if (action) {
                    this.lastRealActionTime = now;
                    this.lastRealDomain = stableDomain;
                    const targetRobot = this.robotSelect.value;
                    console.log(`🤖 REAL ROBOT Trigger (${this.realCooldownMs/1000}s) for ${targetRobot}: ${displayName}`);
                    
                    fetch(`/run_action/${targetRobot}?session_key=${this.sessionKey}`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ action: action })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) console.log(`✅ Real robot confirmed: ${action}`);
                    })
                    .catch(err => console.error('❌ Real robot trigger failed:', err));
                }
            } else {
                // visual feedback
                const wait = Math.ceil((this.realCooldownMs - (now - this.lastRealActionTime)) / 1000);
                this.domainDisplay.textContent = `${displayName} (Hardware Busy ${wait}s)`;
                this.domainDisplay.style.opacity = "0.7";
            }
        } else {
            this.domainDisplay.textContent = '';
            if (this.atmosphereOverlay) {
                this.atmosphereOverlay.style.background = 'transparent';
            }
            if (!this.resetTimer) {
                this.resetTimer = setTimeout(() => {
                    this.lastSimDomain = null;
                    this.lastRealDomain = null;
                    this.lastVFXDomain = null;
                    this.resetTimer = null;
                }, 2000); 
            }
        }
    }
    
    processGestures(multiHandLandmarks) {
        const now = Date.now();
        if (now - this.lastEmitTime < this.emitInterval) return;
        
        const currentHands = multiHandLandmarks.map(landmarks => {
            // Get center point of hand (average of landmarks)
            let x = 0, y = 0;
            landmarks.forEach(l => { x += l.x; y += l.y; });
            return { x: x / landmarks.length, y: y / landmarks.length, raw: landmarks };
        });
        
        if (this.prevHands.length > 0 && currentHands.length > 0) {
            if (currentHands.length === 1 && this.prevHands.length === 1) {
                // ROTATE: 1 hand
                const dx = currentHands[0].x - this.prevHands[0].x;
                const dy = currentHands[0].y - this.prevHands[0].y;
                
                const sensitivity = parseFloat(this.rotateSens.value);
                this.emitControl('rotate', { dx: -dx * sensitivity, dy: dy * sensitivity });
                
            } else if (currentHands.length === 2 && this.prevHands.length === 2) {
                // ZOOM or PAN: 2 hands
                
                // Current distance between hands
                const currentDist = Math.sqrt(
                    Math.pow(currentHands[0].x - currentHands[1].x, 2) + 
                    Math.pow(currentHands[0].y - currentHands[1].y, 2)
                );
                
                // Previous distance
                const prevDist = Math.sqrt(
                    Math.pow(this.prevHands[0].x - this.prevHands[1].x, 2) + 
                    Math.pow(this.prevHands[0].y - this.prevHands[1].y, 2)
                );
                
                // Calculate movement of centers for Panning
                const currentCenter = { 
                    x: (currentHands[0].x + currentHands[1].x) / 2,
                    y: (currentHands[0].y + currentHands[1].y) / 2
                };
                const prevCenter = {
                    x: (this.prevHands[0].x + this.prevHands[1].x) / 2,
                    y: (this.prevHands[0].y + this.prevHands[1].y) / 2
                };
                
                const dx = currentCenter.x - prevCenter.x;
                const dy = currentCenter.y - prevCenter.y;
                
                const dDist = currentDist - prevDist;
                
                // Check if it's primarily a zoom or a pan
                if (Math.abs(dDist) > Math.abs(dx) * 0.4) {
                    // ZOOM
                    const sensitivity = parseFloat(this.zoomSens.value);
                    this.emitControl('zoom', { delta: -dDist * sensitivity });
                } else {
                    // PAN
                    const sensitivity = parseFloat(this.panSens.value);
                    this.emitControl('pan', { dx: -dx * sensitivity, dy: dy * sensitivity });
                }
            }
        }
        
        this.prevHands = currentHands;
        this.lastEmitTime = now;
    }
    
    emitControl(type, params) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify({
                action: 'camera_control',
                session_key: this.sessionKey,
                type: type,
                params: params
            }));
        }
    }
}

window.addEventListener('DOMContentLoaded', () => {
    window.handTracker = new HandTracker();
});
