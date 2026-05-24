
import { AudioPlayer } from './lib/play/AudioPlayer.js';
import { ChatHistoryManager } from "./lib/util/ChatHistoryManager.js";
import { setupRobotModal } from './robotModal.js';
// Setup robot modal popup on page load
document.addEventListener('DOMContentLoaded', () => {
    setupRobotModal();
});

// Connect to the serverless AWS Bedrock AgentCore with authentication via SigV4 signed WebSocket
class NativeSocketEmulator {
    constructor() {
        this.listeners = {};
        this.connected = false;
        this.ws = null;
        this.connectPromise = null;
        
        // Auto-connect in background on load
        this.connect().catch(err => {
            console.error("Auto-connection error on load:", err);
        });
    }
    
    async connect() {
        if (this.connected && this.ws && this.ws.readyState === WebSocket.OPEN) {
            return;
        }
        
        // If there's already an active connection attempt, reuse it
        if (this.connectPromise) {
            return this.connectPromise;
        }
        
        this.connectPromise = (async () => {
            try {
                this.trigger('connecting');
                
                // 1. Fetch Cognito and AgentCore configurations from static config.json
                console.log("Fetching serverless config.json...");
                const configResp = await fetch('/config.json');
                if (!configResp.ok) throw new Error("Could not fetch serverless config.json");
                const config = await configResp.json();
                
                // 2. Retrieve identity ID token from storage
                const idToken = localStorage.getItem('idToken');
                if (!idToken) {
                    console.warn("No ID Token found. Redirecting to login.");
                    window.location.href = '/login.html';
                    return;
                }
                
                // 3. Authenticate with Federated Identity Pool and get credentials
                const providerName = `cognito-idp.${config.region}.amazonaws.com/${config.userPoolId}`;
                console.log("Retrieving temporary AWS credentials from Identity Pool...");
                
                const idResponse = await fetch(`https://cognito-identity.${config.region}.amazonaws.com/`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/x-amz-json-1.1",
                        "X-Amz-Target": "AWSCognitoIdentityService.GetId"
                    },
                    body: JSON.stringify({
                        IdentityPoolId: config.identityPoolId,
                        Logins: {
                            [providerName]: idToken
                        }
                    })
                });
                if (!idResponse.ok) {
                    throw new Error("Failed to retrieve Identity ID from Cognito.");
                }
                const { IdentityId } = await idResponse.json();

                const credsResponse = await fetch(`https://cognito-identity.${config.region}.amazonaws.com/`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/x-amz-json-1.1",
                        "X-Amz-Target": "AWSCognitoIdentityService.GetCredentialsForIdentity"
                    },
                    body: JSON.stringify({
                        IdentityId: IdentityId,
                        Logins: {
                            [providerName]: idToken
                        }
                    })
                });
                if (!credsResponse.ok) {
                    throw new Error("Failed to retrieve temporary AWS credentials from Cognito.");
                }
                const { Credentials } = await credsResponse.json();
                const credentials = {
                    accessKeyId: Credentials.AccessKeyId,
                    secretAccessKey: Credentials.SecretKey,
                    sessionToken: Credentials.SessionToken
                };

                // 4. Load ESM SigV4 signer modules dynamically from ESM CDN
                console.log("Loading ESM Signature modules...");
                const SignatureV4 = (await import('https://esm.sh/@smithy/signature-v4')).SignatureV4;
                const Sha256 = (await import('https://esm.sh/@aws-crypto/sha256-browser')).Sha256;
                const HttpRequest = (await import('https://esm.sh/@smithy/protocol-http')).HttpRequest;

                // 5. Presign the AWS Bedrock AgentCore websocket URL
                const encodedArn = encodeURIComponent(config.runtimeArn);
                const host = `bedrock-agentcore.${config.region}.amazonaws.com`;
                const path = `/runtimes/${encodedArn}/ws`;
                const voiceId = getQueryParams().voice_id || 'tiffany';

                // Get current selection to initialize prompt on connection start
                const selectedRobots = getSelectedRobots();
                const robotsParam = selectedRobots.length > 0 ? selectedRobots.join(',') : 'all';

                const request = new HttpRequest({
                    method: 'GET',
                    protocol: 'https:',
                    hostname: host,
                    path: path,
                    headers: { host },
                    query: { voice_id: voiceId, robots: robotsParam },
                });

                const signer = new SignatureV4({
                    service: 'bedrock-agentcore',
                    region: config.region,
                    credentials,
                    sha256: Sha256,
                });

                console.log("Generating IAM SigV4 pre-signed signature...");
                const signedRequest = await signer.presign(request, {
                    expiresIn: 300,
                });

                const queryParams = new URLSearchParams(signedRequest.query);
                const wsUrl = `wss://${host}${path}?${queryParams.toString()}`;

                console.log(`Connecting to serverless AWS Bedrock AgentCore WebSocket...`);
                this.ws = new WebSocket(wsUrl);
                
                this.ws.onopen = () => {
                    console.log("WebSocket connection established!");
                    this.connected = true;
                    this.trigger('connect');
                };
                
                this.ws.onclose = (event) => {
                    console.log(`WebSocket connection closed: code=${event.code}, reason=${event.reason}`);
                    this.connected = false;
                    this.trigger('disconnect');
                };
                
                this.ws.onerror = (error) => {
                    console.error("WebSocket transport error:", error);
                    this.trigger('error', error);
                };
                
                this.ws.onmessage = (event) => {
                    try {
                        console.log("📥 Raw WebSocket Message from Bedrock AgentCore:", event.data);
                        const payload = JSON.parse(event.data);
                        
                        // 1. Support custom/legacy envelope format
                        if (payload.type) {
                            this.trigger(payload.type, payload);
                        }
                        // 2. Support native Bedrock AgentCore event format
                        else if (payload.event) {
                            const eventKey = Object.keys(payload.event)[0];
                            if (eventKey) {
                                const eventData = payload.event[eventKey];
                                console.log(`👉 Extracted native event '${eventKey}':`, eventData);
                                this.trigger(eventKey, eventData);
                            }
                        }
                    } catch (err) {
                        console.error("Error parsing WebSocket message JSON:", err);
                    }
                };

            } catch (err) {
                console.error("Failed to establish serverless AgentCore connection:", err);
                this.trigger('connect_error', err);
                throw err;
            } finally {
                this.connectPromise = null;
            }
        })();
        
        return this.connectPromise;
    }
    
    on(event, callback) {
        if (!this.listeners[event]) {
            this.listeners[event] = [];
        }
        this.listeners[event].push(callback);
    }
    
    emit(event, data = {}) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            console.warn(`WebSocket is not open. Packet dropped.`);
            return;
        }
        
        let payload = {};
        if (event === 'audioInput') {
            payload = {
                type: 'bidi_audio_input',
                audio: data,
                format: 'pcm',
                sample_rate: 16000,
                channels: 1
            };
        } else if (event === 'robot') {
            payload = {
                type: 'robot',
                robots: data
            };
        } else if (event === 'stopAudio') {
            payload = {
                type: 'stopAudio'
            };
        } else if (event === 'audioStart' || event === 'promptStart' || event === 'systemPrompt') {
            payload = {
                type: event
            };
        } else {
            payload = {
                type: event,
                data: data
            };
        }
        
        this.ws.send(JSON.stringify(payload));
    }
    
    trigger(event, data) {
        const callbacks = this.listeners[event];
        if (callbacks) {
            callbacks.forEach(cb => {
                try {
                    cb(data);
                } catch (e) {
                    console.error(`Error in event listener for ${event}:`, e);
                }
            });
        }
    }
}

const socket = new NativeSocketEmulator();

// DOM elements
const startButton = document.getElementById('start');
const stopButton = document.getElementById('stop');
const statusElement = document.getElementById('status');
const chatContainer = document.getElementById('chat-container');
const robotSelect = document.getElementById('robot-select');

// Chat history management
let chat = { history: [] };
const chatRef = { current: chat };
const chatHistoryManager = ChatHistoryManager.getInstance(
    chatRef,
    (newChat) => {
        chat = { ...newChat };
        chatRef.current = chat;
        updateChatUI();
    }
);

// Audio processing variables
let audioContext;
let audioStream;
let isStreaming = false;
let processor;
let sourceNode;
let waitingForAssistantResponse = false;
let waitingForUserTranscription = false;
let userThinkingIndicator = null;
let assistantThinkingIndicator = null;
let transcriptionReceived = false;
let displayAssistantText = false;
let role;
const audioPlayer = new AudioPlayer();
let sessionInitialized = false;

// Custom system prompt - you can modify this
let SYSTEM_PROMPT = "You are a friend. The user and you will engage in a spoken " +
    "dialog exchanging the transcripts of a natural real-time conversation. Keep your responses short, " +
    "generally two or three sentences for chatty scenarios.";


// Helper to get all selected robots as an array
function getSelectedRobots() {
    const selected = Array.from(robotSelect.selectedOptions).map(opt => opt.value);
    
    if (selected.includes('all')) {
        return [
            "robot_1", "robot_2", "robot_3", "robot_4", "robot_5", "robot_6",
            "drone_1", "drone_2",
            "dog_1", "dog_2", "dog_3",
            "xiaoice_1"
        ];
    }
    
    let result = new Set();
    
    if (selected.includes('all_robots')) {
        for (let i = 1; i <= 6; i++) result.add(`robot_${i}`);
    }
    if (selected.includes('all_drones')) {
        for (let i = 1; i <= 2; i++) result.add(`drone_${i}`);
    }
    if (selected.includes('all_dogs')) {
        for (let i = 1; i <= 3; i++) result.add(`dog_${i}`);
    }
    
    selected.forEach(val => {
        if (!['all', 'all_robots', 'all_drones', 'all_dogs'].includes(val)) {
            result.add(val);
        }
    });
    
    return Array.from(result).filter(val => val !== '');
}

// Add event listener for robot selection (for debug/logging)
robotSelect.addEventListener('change', (event) => {
    console.log(`Selected robots updated: ${getSelectedRobots().join(', ')}`);
});

// Initialize WebSocket audio
async function initAudio() {
    try {
        statusElement.textContent = "Requesting microphone access...";
        statusElement.className = "connecting";

        // Request microphone access
        audioStream = await navigator.mediaDevices.getUserMedia({
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true
            }
        });

        audioContext = new AudioContext({
            sampleRate: 16000
        });

        await audioPlayer.start();

        statusElement.textContent = "Microphone ready. Click Start to begin.";
        statusElement.className = "ready";
        startButton.disabled = false;
    } catch (error) {
        console.error("Error accessing microphone:", error);
        statusElement.textContent = "Error: " + error.message;
        statusElement.className = "error";
    }
}

// Initialize the session with Bedrock
async function initializeSession() {
    if (sessionInitialized) return;

    statusElement.textContent = "Initializing session...";

    try {
        // Ensure WebSocket is connected
        await socket.connect();
        
        // Send events in sequence 
        const robots = getSelectedRobots();
        socket.emit('robot', robots);
        await new Promise(resolve => setTimeout(resolve, 250));
        socket.emit('promptStart');
        socket.emit('systemPrompt');
        await new Promise(resolve => setTimeout(resolve, 1000));

        socket.emit('audioStart');

        // Mark session as initialized
        sessionInitialized = true;
        statusElement.textContent = "Session initialized successfully";
    } catch (error) {
        console.error("Failed to initialize session:", error);
        statusElement.textContent = "Error initializing session";
        statusElement.className = "error";
    }
}

async function startStreaming() {
    if (isStreaming) return;

    try {
        // First, make sure the session is initialized
        if (!sessionInitialized) {
            await initializeSession();
        }

        // Create audio processor
        sourceNode = audioContext.createMediaStreamSource(audioStream);

        // Use ScriptProcessorNode for audio processing
        if (audioContext.createScriptProcessor) {
            processor = audioContext.createScriptProcessor(512, 1, 1);

            processor.onaudioprocess = (e) => {
                if (!isStreaming) return;

                const inputData = e.inputBuffer.getChannelData(0);

                // Convert to 16-bit PCM
                const pcmData = new Int16Array(inputData.length);
                for (let i = 0; i < inputData.length; i++) {
                    pcmData[i] = Math.max(-1, Math.min(1, inputData[i])) * 0x7FFF;
                }

                // Convert to base64 (browser-safe way)
                const base64Data = arrayBufferToBase64(pcmData.buffer);

                // Send to server
                socket.emit('audioInput', base64Data);
            };

            sourceNode.connect(processor);
            processor.connect(audioContext.destination);
        }

        isStreaming = true;
        startButton.disabled = true;
        stopButton.disabled = false;
        statusElement.textContent = "Streaming... Speak now";
        statusElement.className = "recording";

        // Show user thinking indicator when starting to record
        transcriptionReceived = false;
        showUserThinkingIndicator();

    } catch (error) {
        console.error("Error starting recording:", error);
        statusElement.textContent = "Error: " + error.message;
        statusElement.className = "error";
    }
}

// Convert ArrayBuffer to base64 string
function arrayBufferToBase64(buffer) {
    const binary = [];
    const bytes = new Uint8Array(buffer);
    for (let i = 0; i < bytes.byteLength; i++) {
        binary.push(String.fromCharCode(bytes[i]));
    }
    return btoa(binary.join(''));
}

// Parse URL query parameters
function getQueryParams() {
    const params = {};
    const queryString = window.location.search.substring(1);
    const pairs = queryString.split('&');

    for (let i = 0; i < pairs.length; i++) {
        if (!pairs[i]) continue;
        const pair = pairs[i].split('=');
        params[decodeURIComponent(pair[0])] = decodeURIComponent(pair[1] || '');
    }

    return params;
}

function stopStreaming() {
    if (!isStreaming) return;

    isStreaming = false;

    // Clean up audio processing
    if (processor) {
        processor.disconnect();
        sourceNode.disconnect();
    }

    startButton.disabled = false;
    stopButton.disabled = true;
    statusElement.textContent = "Processing...";
    statusElement.className = "processing";

    audioPlayer.stop();
    // Tell server to finalize processing
    socket.emit('stopAudio');

    // End the current turn in chat history
    chatHistoryManager.endTurn();
}

// Base64 to Float32Array conversion
function base64ToFloat32Array(base64String) {
    try {
        const binaryString = window.atob(base64String);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }

        const int16Array = new Int16Array(bytes.buffer);
        const float32Array = new Float32Array(int16Array.length);
        for (let i = 0; i < int16Array.length; i++) {
            float32Array[i] = int16Array[i] / 32768.0;
        }

        return float32Array;
    } catch (error) {
        console.error('Error in base64ToFloat32Array:', error);
        throw error;
    }
}

// Process message data and add to chat history
function handleTextOutput(data) {
    console.log("Processing text output:", data);
    if (data.content) {
        const messageData = {
            role: data.role,
            message: data.content
        };
        chatHistoryManager.addTextMessage(messageData);
    }
}

// Update the UI based on the current chat history
function updateChatUI() {
    if (!chatContainer) {
        console.error("Chat container not found");
        return;
    }

    // Clear existing chat messages
    chatContainer.innerHTML = '';

    // Add all messages from history
    chat.history.forEach(item => {
        if (item.endOfConversation) {
            const endDiv = document.createElement('div');
            endDiv.className = 'message system';
            endDiv.textContent = "Conversation ended";
            chatContainer.appendChild(endDiv);
            return;
        }

        if (item.role) {
            const messageDiv = document.createElement('div');
            const roleLowerCase = item.role.toLowerCase();
            messageDiv.className = `message ${roleLowerCase}`;

            const roleLabel = document.createElement('div');
            roleLabel.className = 'role-label';
            roleLabel.textContent = item.role;
            messageDiv.appendChild(roleLabel);

            const content = document.createElement('div');
            content.textContent = item.message || "No content";
            messageDiv.appendChild(content);

            chatContainer.appendChild(messageDiv);
        }
    });

    // Re-add thinking indicators if we're still waiting
    if (waitingForUserTranscription) {
        showUserThinkingIndicator();
    }

    if (waitingForAssistantResponse) {
        showAssistantThinkingIndicator();
    }

    // Scroll to bottom
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Show the "Listening" indicator for user
function showUserThinkingIndicator() {
    hideUserThinkingIndicator();

    waitingForUserTranscription = true;
    userThinkingIndicator = document.createElement('div');
    userThinkingIndicator.className = 'message user thinking';

    const roleLabel = document.createElement('div');
    roleLabel.className = 'role-label';
    roleLabel.textContent = 'USER';
    userThinkingIndicator.appendChild(roleLabel);

    const listeningText = document.createElement('div');
    listeningText.className = 'thinking-text';
    listeningText.textContent = 'Listening';
    userThinkingIndicator.appendChild(listeningText);

    const dotContainer = document.createElement('div');
    dotContainer.className = 'thinking-dots';

    for (let i = 0; i < 3; i++) {
        const dot = document.createElement('span');
        dot.className = 'dot';
        dotContainer.appendChild(dot);
    }

    userThinkingIndicator.appendChild(dotContainer);
    chatContainer.appendChild(userThinkingIndicator);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Show the "Thinking" indicator for assistant
function showAssistantThinkingIndicator() {
    hideAssistantThinkingIndicator();

    waitingForAssistantResponse = true;
    assistantThinkingIndicator = document.createElement('div');
    assistantThinkingIndicator.className = 'message assistant thinking';

    const roleLabel = document.createElement('div');
    roleLabel.className = 'role-label';
    roleLabel.textContent = 'ASSISTANT';
    assistantThinkingIndicator.appendChild(roleLabel);

    const thinkingText = document.createElement('div');
    thinkingText.className = 'thinking-text';
    thinkingText.textContent = 'Thinking';
    assistantThinkingIndicator.appendChild(thinkingText);

    const dotContainer = document.createElement('div');
    dotContainer.className = 'thinking-dots';

    for (let i = 0; i < 3; i++) {
        const dot = document.createElement('span');
        dot.className = 'dot';
        dotContainer.appendChild(dot);
    }

    assistantThinkingIndicator.appendChild(dotContainer);
    chatContainer.appendChild(assistantThinkingIndicator);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Hide the user thinking indicator
function hideUserThinkingIndicator() {
    waitingForUserTranscription = false;
    if (userThinkingIndicator && userThinkingIndicator.parentNode) {
        userThinkingIndicator.parentNode.removeChild(userThinkingIndicator);
    }
    userThinkingIndicator = null;
}

// Hide the assistant thinking indicator
function hideAssistantThinkingIndicator() {
    waitingForAssistantResponse = false;
    if (assistantThinkingIndicator && assistantThinkingIndicator.parentNode) {
        assistantThinkingIndicator.parentNode.removeChild(assistantThinkingIndicator);
    }
    assistantThinkingIndicator = null;
}

// EVENT HANDLERS
// --------------

// Handle content start from the server
socket.on('contentStart', (data) => {
    console.log('Content start received:', data);

    if (data.type === 'TEXT') {
        // Below update will be enabled when role is moved to the contentStart
        role = data.role;
        if (data.role === 'USER') {
            // When user's text content starts, hide user thinking indicator
            hideUserThinkingIndicator();
        }
        else if (data.role === 'ASSISTANT') {
            // When assistant's text content starts, hide assistant thinking indicator
            hideAssistantThinkingIndicator();
            let isSpeculative = false;
            try {
                if (data.additionalModelFields) {
                    const additionalFields = JSON.parse(data.additionalModelFields);
                    isSpeculative = additionalFields.generationStage === "SPECULATIVE";
                    if (isSpeculative) {
                        console.log("Received speculative content");
                        displayAssistantText = true;
                    }
                    else {
                        displayAssistantText = false;
                    }
                }
            } catch (e) {
                console.error("Error parsing additionalModelFields:", e);
            }
        }
    }
    else if (data.type === 'AUDIO') {
        // When audio content starts, we may need to show user thinking indicator
        if (isStreaming) {
            showUserThinkingIndicator();
        }
    }
});

// Handle text output from the server
socket.on('textOutput', (data) => {
    console.log('Received text output:', data);

    if (role === 'USER') {
        // When user text is received, show thinking indicator for assistant response
        transcriptionReceived = true;
        //hideUserThinkingIndicator();

        // Add user message to chat
        handleTextOutput({
            role: data.role,
            content: data.content
        });

        // Show assistant thinking indicator after user text appears
        showAssistantThinkingIndicator();
    }
    else if (role === 'ASSISTANT') {
        //hideAssistantThinkingIndicator();
        if (displayAssistantText) {
            handleTextOutput({
                role: data.role,
                content: data.content
            });
        }
    }
});

// Handle audio output
socket.on('audioOutput', (data) => {
    if (data.content) {
        try {
            const audioData = base64ToFloat32Array(data.content);
            audioPlayer.playAudio(audioData);
        } catch (error) {
            console.error('Error processing audio data:', error);
        }
    }
});

// Handle content end events
socket.on('contentEnd', (data) => {
    console.log('Content end received:', data);

    if (data.type === 'TEXT') {
        if (role === 'USER') {
            // When user's text content ends, make sure assistant thinking is shown
            hideUserThinkingIndicator();
            showAssistantThinkingIndicator();
        }
        else if (role === 'ASSISTANT') {
            // When assistant's text content ends, prepare for user input in next turn
            hideAssistantThinkingIndicator();
        }

        // Handle stop reasons
        if (data.stopReason && data.stopReason.toUpperCase() === 'END_TURN') {
            chatHistoryManager.endTurn();
        } else if (data.stopReason && data.stopReason.toUpperCase() === 'INTERRUPTED') {
            console.log("Interrupted by user");
            audioPlayer.bargeIn();
        }
    }
    else if (data.type === 'AUDIO') {
        // When audio content ends, we may need to show user thinking indicator
        if (isStreaming) {
            showUserThinkingIndicator();
        }
    }
});

// Stream completion event
socket.on('streamComplete', () => {
    if (isStreaming) {
        stopStreaming();
    }
    statusElement.textContent = "Ready";
    statusElement.className = "ready";
});

// Handle connection status updates
socket.on('connect', () => {
    statusElement.textContent = "Connected to server";
    statusElement.className = "connected";
    sessionInitialized = false;
});

socket.on('disconnect', () => {
    console.log("WebSocket disconnected. Cleaning up streaming state...");
    
    // Clean up audio processing if active
    if (isStreaming) {
        isStreaming = false;
        if (processor) {
            try {
                processor.disconnect();
                sourceNode.disconnect();
            } catch (e) {
                console.warn("Error disconnecting audio nodes:", e);
            }
        }
        audioPlayer.stop();
    }

    statusElement.textContent = "Session ended (finished or timed out). Click Start to resume.";
    statusElement.className = "disconnected";
    startButton.disabled = false; // Keep start button enabled for instant reconnection!
    stopButton.disabled = true;
    sessionInitialized = false;
    hideUserThinkingIndicator();
    hideAssistantThinkingIndicator();
});

socket.on('connect_error', (error) => {
    console.error("Connection error:", error);
    if (error && error.message && error.message.includes('Authentication error')) {
        // Authentication failed, redirect to login
        localStorage.clear();
        window.location.href = '/login.html';
    } else {
        statusElement.textContent = "Connection error: " + (error.message || error);
        statusElement.className = "error";
        startButton.disabled = false; // Allow retrying connection
        stopButton.disabled = true;
    }
});

// Handle errors
socket.on('error', (error) => {
    console.error("Server error:", error);
    statusElement.textContent = "Error: " + (error.message || JSON.stringify(error).substring(0, 100));
    statusElement.className = "error";
    startButton.disabled = false; // Allow restarting session on error
    stopButton.disabled = true;
    hideUserThinkingIndicator();
    hideAssistantThinkingIndicator();
});

// Button event listeners
startButton.addEventListener('click', startStreaming);
stopButton.addEventListener('click', stopStreaming);

// Initialize the app when the page loads
document.addEventListener('DOMContentLoaded', async () => {
    await initAudio();

    // Check for robot parameter in URL
    const params = getQueryParams();
    if (params.robot) {
        // Set robot selection
        const robotValue = params.robot;
        if (robotSelect.querySelector(`option[value="${robotValue}"]`)) {
            robotSelect.value = robotValue;
            console.log(`Auto-selected robot: ${robotValue} from URL parameter`);

            // Start streaming after a short delay
            setTimeout(() => {
                console.log("Auto-starting streaming...");
                startStreaming();
            }, 3000);
        }
    }
});

// Auto-start if robot parameter is present
const queryParams = getQueryParams();
if (queryParams.robot) {
    robotSelect.value = queryParams.robot;
    console.log(`Auto-selected robot: ${queryParams.robot}`);
    initAudio();
}