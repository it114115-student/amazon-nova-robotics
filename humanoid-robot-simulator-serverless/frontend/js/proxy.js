// Action configuration dictionary
const actions = {
    "back_fast": { "sleep_time": 4.5, "action": ["2", "4"], "name": "back_fast" },
    "bow": { "sleep_time": 4, "action": ["10", "1"], "name": "bow" },
    "chest": { "sleep_time": 9, "action": ["12", "1"], "name": "chest" },
    "dance_eight": { "sleep_time": 85, "action": ["42", "1"], "name": "dance_eight" },
    "dance_five": { "sleep_time": 59, "action": ["39", "1"], "name": "dance_five" },
    "dance_four": { "sleep_time": 59, "action": ["38", "1"], "name": "dance_four" },
    "dance_nine": { "sleep_time": 84, "action": ["43", "1"], "name": "dance_nine" },
    "dance_seven": { "sleep_time": 67, "action": ["41", "1"], "name": "dance_seven" },
    "dance_six": { "sleep_time": 69, "action": ["40", "1"], "name": "dance_six" },
    "dance_ten": { "sleep_time": 85, "action": ["44", "1"], "name": "dance_ten" },
    "dance_three": { "sleep_time": 70, "action": ["37", "1"], "name": "dance_three" },
    "dance_two": { "sleep_time": 52, "action": ["36", "1"], "name": "dance_two" },
    "go_forward": { "sleep_time": 3.5, "action": ["1", "4"], "name": "go_forward" },
    "kung_fu": { "sleep_time": 2, "action": ["46", "2"], "name": "kung_fu" },
    "left_kick": { "sleep_time": 2, "action": ["18", "1"], "name": "left_kick" },
    "left_move_fast": { "sleep_time": 3, "action": ["3", "4"], "name": "left_move_fast" },
    "left_shot_fast": { "sleep_time": 4, "action": ["13", "1"], "name": "left_shot_fast" },
    "left_uppercut": { "sleep_time": 2, "action": ["16", "1"], "name": "left_uppercut" },
    "push_ups": { "sleep_time": 9, "action": ["5", "1"], "name": "push_ups" },
    "right_kick": { "sleep_time": 2, "action": ["19", "1"], "name": "right_kick" },
    "right_move_fast": { "sleep_time": 3, "action": ["4", "4"], "name": "right_move_fast" },
    "right_shot_fast": { "sleep_time": 4, "action": ["14", "1"], "name": "right_shot_fast" },
    "right_uppercut": { "sleep_time": 2, "action": ["17", "1"], "name": "right_uppercut" },
    "sit_ups": { "sleep_time": 12, "action": ["6", "1"], "name": "sit_ups" },
    "squat": { "sleep_time": 1, "action": ["11", "1"], "name": "squat" },
    "squat_up": { "sleep_time": 6, "action": ["45", "1"], "name": "squat_up" },
    "stand": { "sleep_time": 1, "action": ["0", "1"], "name": "stand" },
    "stand_up_back": { "sleep_time": 5, "action": ["21", "1"], "name": "stand_up_back" },
    "stand_up_front": { "sleep_time": 5, "action": ["20", "1"], "name": "stand_up_front" },
    "stepping": { "sleep_time": 3, "action": ["24", "2"], "name": "stepping" },
    "stop": { "sleep_time": 3, "action": ["24", "2"], "name": "stop" },
    "turn_left": { "sleep_time": 4, "action": ["7", "4"], "name": "turn_left" },
    "turn_right": { "sleep_time": 4, "action": ["8", "4"], "name": "turn_right" },
    "twist": { "sleep_time": 4, "action": ["22", "1"], "name": "twist" },
    "wave": { "sleep_time": 3.5, "action": ["9", "1"], "name": "wave" },
    "weightlifting": { "sleep_time": 9, "action": ["35", "1"], "name": "weightlifting" },
    "wing_chun": { "sleep_time": 2, "action": ["15", "1"], "name": "wing_chun" }
};

// Idle action
const idleAction = { "name": null, "sleep_time": 0 };

class ActionExecutor {
    constructor(robotId, simulatorEndpoint, sessionKey) {
        this.robotId = robotId;
        this.simulatorEndpoint = simulatorEndpoint;
        this.sessionKey = sessionKey;
        this.actionQueue = [];
        this.currentAction = { ...idleAction };
        this.isRunning = false;
        this.immediateStopEvent = false;
        this.queueLock = false;
        this.stopEvent = false;
        this.consumerInterval = null;
        this.currentActionTimeout = null;

        this.startConsumer();
    }

    generateId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }

    async runAction(actionName, p1, p2) {
        try {
            // Send to simulator
            await this.sendToSimulator(
                actionName,
                `Action ${actionName} sent to simulator.`,
                `Error sending action ${actionName} to simulator:`
            );

            // Send JSON-RPC request
            return await this.sendRequest(
                "RunAction",
                [p1, p2],
                `Action ${actionName} run_action(${p1}, ${p2}) successful.`,
                `Error running action ${actionName} run_action(${p1}, ${p2}):`
            );
        } catch (error) {
            console.error(`Error in runAction: ${error}`);
            return null;
        }
    }

    async runStopAction() {
        return await this.sendRequest(
            "StopBusServo",
            ["stopAction"],
            "Action run_stop_action() successful.",
            "Error running action run_stop_action():"
        );
    }

    async sendRequest(method, params, logSuccessMsg, logErrorMsg) {
        const headers = {
            "deviceid": "1732853986186",
            "Content-Type": "application/json"
        };
        const data = {
            "id": "1732853986186",
            "jsonrpc": "2.0",
            "method": method
        };
        if (params !== null) {
            data.params = params;
        }

        try {
            const response = await fetch("http://localhost:9031/", {
                method: "POST",
                headers: headers,
                body: JSON.stringify(data),
                signal: AbortSignal.timeout(1000)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            console.log(`${logSuccessMsg} Response:`, result);
            return result;
        } catch (error) {
            console.error(`${logErrorMsg}`, error);
            return null;
        }
    }

    async executeAction(actionItem) {
        const actionName = actionItem.name;
        const action = actions[actionName];

        this.currentAction = {
            name: action.name,
            sleep_time: action.sleep_time
        };

        try {
            console.log(`Sending action ${actionName} to robot...`);
            await this.runAction(actionName, action.action[0], action.action[1]);

            const sleepTime = action.sleep_time * 1000; // Convert to milliseconds
            console.log(`Waiting ${action.sleep_time} seconds for action ${actionName} to complete...`);

            let elapsed = 0;
            const checkInterval = 100; // Check every 100ms

            return new Promise((resolve) => {
                this.currentActionTimeout = setInterval(() => {
                    if (this.immediateStopEvent) {
                        console.log(`Stopping action execution for ${actionName}`);
                        clearInterval(this.currentActionTimeout);
                        this.immediateStopEvent = false;
                        this.runStopAction();
                        this.currentAction = { ...idleAction };
                        resolve();
                        return;
                    }

                    elapsed += checkInterval;
                    if (elapsed >= sleepTime) {
                        console.log(`Action ${actionName} completed after ${elapsed / 1000} seconds`);
                        clearInterval(this.currentActionTimeout);
                        this.currentAction = { ...idleAction };
                        resolve();
                    }
                }, checkInterval);
            });

        } catch (error) {
            console.error(`Error executing action ${actionName}:`, error);
            this.currentAction = { ...idleAction };
            throw error; // Re-throw to ensure proper error handling in processQueue
        }
    }

    removeActionById(actionId) {
        if (this.queueLock) return;

        this.queueLock = true;
        this.actionQueue = this.actionQueue.filter(item => item.id !== actionId);
        this.queueLock = false;
    }

    startConsumer() {
        // Wait for 5-second alignment (like Python version)
        const delay = 5000 - (Date.now() % 5000);
        console.log(`ActionExecutor: Starting consumer in ${delay}ms to align with 5-second intervals`);

        setTimeout(() => {
            console.log('ActionExecutor: Consumer started, processing queue every 1 second');
            this.consumerInterval = setInterval(() => {
                this.processQueue();
            }, 1000); // Process queue every second like Python
        }, delay);
    }

    async processQueue() {
        if (this.stopEvent) {
            clearInterval(this.consumerInterval);
            return;
        }

        if (this.immediateStopEvent) {
            console.log("Immediate stop triggered, clearing queue and setting to idle.");
            this.clearActionQueue();
            this.currentAction = { ...idleAction };
            this.isRunning = false;
            this.immediateStopEvent = false;
            return;
        }

        if (this.actionQueue.length > 0 && !this.isRunning) {
            // Get the first action but don't remove it yet (like Python version)
            const actionItem = this.actionQueue[0];
            this.isRunning = true;

            console.log(`Starting action: ${actionItem.name}, queue length: ${this.actionQueue.length}`);

            try {
                // Execute action and wait for its sleep_time to complete
                await this.executeAction(actionItem);

                console.log(`Completed action: ${actionItem.name}`);

                // Now remove the completed action from queue
                this.removeActionById(actionItem.id);

                // Add delay before processing next action (like Python version)
                setTimeout(() => {
                    this.isRunning = false;
                }, 500);
            } catch (error) {
                console.error(`Error processing action ${actionItem.name}:`, error);
                this.removeActionById(actionItem.id);
                this.isRunning = false;
            }
        } else if (this.actionQueue.length === 0) {
            this.isRunning = false;
        }
    }

    addActionToQueue(actionName) {
        const actionId = this.generateId();

        if (actionName === "stop") {
            this.stop();
            return;
        }

        if (!(actionName in actions)) {
            console.error(`Action '${actionName}' not found in actions dictionary.`);
            return;
        }

        if (!this.queueLock) {
            this.queueLock = true;
            this.actionQueue.push({ id: actionId, name: actionName });
            this.queueLock = false;
        }
    }

    removeActionFromQueue(actionId) {
        this.removeActionById(actionId);
    }

    clearActionQueue() {
        if (!this.queueLock) {
            this.queueLock = true;
            this.actionQueue = [];
            this.queueLock = false;
        }
    }

    getQueueStatus() {
        return {
            queue: [...this.actionQueue],
            current_action: this.currentAction,
            is_running: this.isRunning
        };
    }

    stop() {
        console.log("Immediate stop requested: clearing queue and interrupting current action.");
        this.immediateStopEvent = true;
        this.clearActionQueue();

        // Add stand action after clearing
        if (!this.queueLock) {
            this.queueLock = true;
            const standId = this.generateId();
            this.actionQueue.push({ id: standId, name: "stand" });
            this.queueLock = false;
        }
    }

    shutdown() {
        this.stopEvent = true;
        if (this.consumerInterval) {
            clearInterval(this.consumerInterval);
        }
        if (this.currentActionTimeout) {
            clearInterval(this.currentActionTimeout);
        }
    }

    async sendToSimulator(actionName, logSuccessMsg = null, logErrorMsg = null) {
        if (logSuccessMsg === null) {
            logSuccessMsg = `Simulator action ${actionName} for robot ${this.robotId} successful.`;
        }
        if (logErrorMsg === null) {
            logErrorMsg = `Error sending action ${actionName} to simulator for robot ${this.robotId}:`;
        }

        const url = `${this.simulatorEndpoint}/run_action/${this.robotId}?session_key=hkiitrobot`;
        const payload = { action: actionName };

        try {
            const response = await fetch(url, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
                signal: AbortSignal.timeout(3000)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            console.log(`${this.robotId} - ${logSuccessMsg} Response:`, result);
            return result;
        } catch (error) {
            console.error(`${logErrorMsg}`, error);
            return null;
        }
    }


}

class ActionEventsProxy {
    constructor() {
        this.socket = null;
        this.sessionKey = window.sessionKey; // Will be set from HTML
        this.events = [];
        this.startTime = new Date();
        this.autoScroll = true;
        this.currentFilter = 'all';
        this.stats = {
            total: 0,
            actions: 0,
            errors: 0
        };

        // ActionExecutor integration
        // Get robotId from query parameter 'robot_id', fallback to window.robot_1 or 'robot_1'
        const urlParams = new URLSearchParams(window.location.search);
        this.robotId = urlParams.get('robot_id') || window.robot_1 || 'robot_1';

        // Determine the appropriate endpoint based on current location
        // const currentHost = window.location.host;
        // if (currentHost.includes('localhost') || currentHost.includes('127.0.0.1')) {
        //     // Use local development server
        //     this.simulatorEndpoint = window.simulatorEndpoint || `${window.location.protocol}//${window.location.host}`;
        // } else {
        //     // Use production Cloud Run endpoint
        //     this.simulatorEndpoint = window.simulatorEndpoint || 'https://humanoid-robot-simulator-74gfpibg5q-uc.a.run.app';
        // }
        this.simulatorEndpoint = window.simulatorEndpoint || 'https://humanoid-robot-simulator-74gfpibg5q-uc.a.run.app';


        console.log('🌐 Using simulator endpoint:', this.simulatorEndpoint);
        this.actionExecutor = null;

        this.init();
    }

    init() {
        console.log('🚀 Initializing Action Events Proxy...');

        // Update the UI with the current endpoint
        const endpointElement = document.getElementById('simulator-endpoint');
        if (endpointElement) {
            endpointElement.textContent = this.simulatorEndpoint;
        }

        this.setupEventFilters();
        this.startUptimeCounter();
        this.connectToSession();

        // Initialize ActionExecutor
        if (this.sessionKey && this.robotId) {
            this.actionExecutor = new ActionExecutor(
                this.robotId,
                this.simulatorEndpoint,
                this.sessionKey
            );
            console.log('✅ ActionExecutor initialized');
            this.startStatusUpdates();
        } else {
            console.warn('⚠️ Missing sessionKey or robotId for ActionExecutor');
        }
    }

    connectToSession() {
        console.log(`🔌 Connecting to session: ${this.sessionKey}`);

        // Support local testing overrides
        const urlParams = new URLSearchParams(window.location.search);
        let wsUrl = '';
        if (urlParams.has('ws_url')) {
            wsUrl = urlParams.get('ws_url');
        } else {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            wsUrl = `${protocol}//${window.location.host}/ws?session_key=${this.sessionKey}`;
        }

        console.log(`🔗 Connecting to: ${wsUrl}`);
        this.socket = new WebSocket(wsUrl);

        this.socket.onopen = () => {
            console.log('✅ Connected to WebSocket server');
            this.updateConnectionStatus(true);

            // Join the session explicitly (APIGW WebSocket routing)
            this.socket.send(JSON.stringify({
                action: 'join_session',
                session_key: this.sessionKey
            }));
        };

        this.socket.onclose = () => {
            console.log('❌ Disconnected from WebSocket server');
            this.updateConnectionStatus(false);
        };

        this.socket.onerror = (error) => {
            console.error('❌ WebSocket error:', error);
            this.addEvent('error', error);
        };

        this.socket.onmessage = (event) => {
            try {
                const payload = JSON.parse(event.data);
                const eventType = payload.type;
                const data = payload.data;

                console.log(`📡 Received ${eventType}:`, data);
                this.addEvent(eventType, data);

                // Handle actions events by executing the action
                if (eventType === 'actions' && data && data.action_name) {
                    console.log(`🎯 Auto-executing action from WebSocket: ${data.action_name}`);
                    const robotId = new URLSearchParams(window.location.search).get('robot_id') || this.robotId;
                    if (data.robot_id === "all")
                        this.executeAction(data.action_name);
                    if (data.robot_id && data.robot_id !== robotId) {
                        // Ignore actions for other robots
                        return;
                    }
                    this.executeAction(data.action_name);
                }
            } catch (e) {
                console.error('❌ Failed to parse WebSocket JSON message:', e, event.data);
            }
        };
    }

    subscribeToEvents() {
        console.log('✅ Native WebSocket event routing is self-contained');
    }

    addEvent(type, data) {
        const timestamp = new Date();
        const event = {
            id: Date.now() + Math.random(),
            type: type,
            data: data,
            timestamp: timestamp,
            timeString: timestamp.toLocaleTimeString()
        };

        this.events.unshift(event); // Add to beginning for newest first
        this.updateStats(type);
        this.renderEvent(event);
        this.updateEventsCount();

        // Limit events to prevent memory issues
        if (this.events.length > 1000) {
            this.events = this.events.slice(0, 1000);
        }
    }

    renderEvent(event) {
        const eventsList = document.getElementById('events-list');
        const eventElement = this.createEventElement(event);

        // Check if event matches current filter
        if (this.shouldShowEvent(event)) {
            eventsList.insertBefore(eventElement, eventsList.firstChild);

            if (this.autoScroll) {
                eventElement.scrollIntoView({ behavior: 'smooth' });
            }
        }
    }

    createEventElement(event) {
        const div = document.createElement('div');
        div.className = `event-item ${this.getEventClass(event.type)}`;
        div.setAttribute('data-filter', event.type);

        div.innerHTML = `
            <div class="event-header">
                <span class="event-type">${event.type}</span>
                <span class="event-time">${event.timeString}</span>
            </div>
            <div class="event-data">${JSON.stringify(event.data, null, 2)}</div>
        `;

        return div;
    }

    getEventClass(eventType) {
        if (eventType.includes('error')) return 'error';
        if (eventType.includes('warning')) return 'warning';
        return '';
    }

    shouldShowEvent(event) {
        if (this.currentFilter === 'all') return true;

        switch (this.currentFilter) {
            case 'robot_action':
                return event.type === 'robot_action' || event.type === 'actions';
            case 'action_result':
                return event.type === 'action_result';
            case 'robot_states':
                return event.type === 'robot_states';
            case 'error':
                return event.type.includes('error');
            case 'video':
                return event.type.includes('video');
            default:
                return event.type === this.currentFilter;
        }
    }

    updateStats(eventType) {
        this.stats.total++;

        if (eventType === 'robot_action' || eventType === 'actions') {
            this.stats.actions++;
        }

        if (eventType.includes('error')) {
            this.stats.errors++;
        }

        document.getElementById('total-events').textContent = this.stats.total;
        document.getElementById('action-events').textContent = this.stats.actions;
        document.getElementById('error-events').textContent = this.stats.errors;
    }

    updateEventsCount() {
        const visibleEvents = document.querySelectorAll('.event-item:not([style*="display: none"])').length;
        document.getElementById('events-count').textContent = `${visibleEvents} events`;
    }

    updateConnectionStatus(connected) {
        const statusDot = document.getElementById('status-dot');
        const statusText = document.getElementById('connection-status');

        if (connected) {
            statusDot.className = 'status-dot connected';
            statusText.textContent = 'Connected';
        } else {
            statusDot.className = 'status-dot disconnected';
            statusText.textContent = 'Disconnected';
        }
    }

    setupEventFilters() {
        const filterButtons = document.querySelectorAll('.filter-btn');

        filterButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                filterButtons.forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');

                this.currentFilter = e.target.getAttribute('data-filter');
                this.filterEvents();
            });
        });
    }

    filterEvents() {
        const eventItems = document.querySelectorAll('.event-item');

        eventItems.forEach(item => {
            const eventType = item.getAttribute('data-filter');
            const shouldShow = this.currentFilter === 'all' || this.shouldShowEventByType(eventType);

            item.style.display = shouldShow ? 'block' : 'none';
        });

        this.updateEventsCount();
    }

    shouldShowEventByType(eventType) {
        switch (this.currentFilter) {
            case 'robot_action':
                return eventType === 'robot_action' || eventType === 'actions';
            case 'action_result':
                return eventType === 'action_result';
            case 'robot_states':
                return eventType === 'robot_states';
            case 'error':
                return eventType.includes('error');
            case 'video':
                return eventType.includes('video');
            default:
                return eventType === this.currentFilter;
        }
    }

    startUptimeCounter() {
        setInterval(() => {
            const uptime = new Date() - this.startTime;
            const hours = Math.floor(uptime / 3600000);
            const minutes = Math.floor((uptime % 3600000) / 60000);
            const seconds = Math.floor((uptime % 60000) / 1000);

            document.getElementById('uptime').textContent =
                `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }, 1000);
    }

    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
            console.log('🔌 Manually disconnected from WebSocket server');
        }

        if (this.actionExecutor) {
            this.actionExecutor.shutdown();
            console.log('🛑 ActionExecutor shutdown');
        }
    }

    clearEvents() {
        this.events = [];
        document.getElementById('events-list').innerHTML = '';
        this.stats = { total: 0, actions: 0, errors: 0 };
        this.updateStats('');
        this.updateEventsCount();
        console.log('🗑️ Events cleared');
    }

    exportEvents() {
        const data = JSON.stringify(this.events, null, 2);
        const blob = new Blob([data], { type: 'application/json' });
        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.href = url;
        a.download = `robot-events-${this.sessionKey}-${new Date().toISOString().slice(0, 19)}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        console.log('📥 Events exported');
    }

    toggleAutoScroll() {
        this.autoScroll = !this.autoScroll;
        document.getElementById('autoscroll-text').textContent =
            `📜 Auto-scroll: ${this.autoScroll ? 'ON' : 'OFF'}`;
        console.log(`📜 Auto-scroll ${this.autoScroll ? 'enabled' : 'disabled'}`);
    }

    updateActionStatus() {
        if (!this.actionExecutor) return;

        const status = this.actionExecutor.getQueueStatus();

        // Update status display if elements exist
        const statusElement = document.getElementById('action-status');
        if (statusElement) {
            statusElement.innerHTML = `
                <div class="action-status">
                    <strong>Current Action:</strong> ${status.current_action.name || 'Idle'}
                    <br>
                    <strong>Queue Length:</strong> ${status.queue.length}
                    <br>
                    <strong>Is Running:</strong> ${status.is_running ? 'Yes' : 'No'}
                </div>
            `;
        }

        // Update queue display if element exists
        const queueElement = document.getElementById('action-queue');
        if (queueElement) {
            queueElement.innerHTML = status.queue.map(item =>
                `<div class="queue-item">${item.name}</div>`
            ).join('');
        }
    }

    startStatusUpdates() {
        // Update action status every second
        setInterval(() => {
            this.updateActionStatus();
        }, 1000);
    }

    // ActionExecutor integration methods
    executeAction(actionName) {
        if (!this.actionExecutor) {
            console.error('❌ ActionExecutor not initialized');
            return;
        }

        console.log(`🎯 Executing action: ${actionName}`);
        this.actionExecutor.addActionToQueue(actionName);

        // Add event for tracking
        this.addEvent('action_queued', {
            action: actionName,
            timestamp: new Date().toISOString()
        });
    }

    stopActions() {
        if (!this.actionExecutor) {
            console.error('❌ ActionExecutor not initialized');
            return;
        }

        console.log('🛑 Stopping all actions');
        this.actionExecutor.stop();

        this.addEvent('actions_stopped', {
            timestamp: new Date().toISOString()
        });
    }

    clearActionQueue() {
        if (!this.actionExecutor) {
            console.error('❌ ActionExecutor not initialized');
            return;
        }

        console.log('🗑️ Clearing action queue');
        this.actionExecutor.clearActionQueue();

        this.addEvent('queue_cleared', {
            timestamp: new Date().toISOString()
        });
    }

    getActionQueueStatus() {
        if (!this.actionExecutor) {
            console.error('❌ ActionExecutor not initialized');
            return null;
        }

        return this.actionExecutor.getQueueStatus();
    }
}

// Global functions for action execution
function executeAction(actionName) {
    if (proxy) {
        proxy.executeAction(actionName);
    }
}

function stopActions() {
    if (proxy) {
        proxy.stopActions();
    }
}

function clearActionQueue() {
    if (proxy) {
        proxy.clearActionQueue();
    }
}

function getActionQueueStatus() {
    if (proxy) {
        return proxy.getActionQueueStatus();
    }
    return null;
}

function getAvailableActions() {
    return Object.keys(actions);
}

function getActionDetails(actionName) {
    return actions[actionName] || null;
}

function getAllActionDetails() {
    return actions;
}

// Global functions for button handlers
let proxy;

function connectToSession() {
    if (proxy) {
        proxy.connectToSession();
    }
}

function disconnect() {
    if (proxy) {
        proxy.disconnect();
    }
}

function clearEvents() {
    if (proxy) {
        proxy.clearEvents();
    }
}

function exportEvents() {
    if (proxy) {
        proxy.exportEvents();
    }
}

function toggleAutoScroll() {
    if (proxy) {
        proxy.toggleAutoScroll();
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    proxy = new ActionEventsProxy();
});
