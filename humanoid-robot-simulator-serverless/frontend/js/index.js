// Additional initialization and debugging
console.log('🚀 3D Robot Simulator HTML template loaded');

// Function to run predefined action sequences
function runSequence(sequenceType) {
    if (!window.simulator) {
        console.error('❌ Simulator not initialized');
        return;
    }

    // Check if an action is already in progress
    if (window.simulator.isActionInProgress) {
        alert(`⚠️ Please wait - ${window.simulator.currentActionName} is still in progress for ${window.simulator.currentActionRobot}`);
        return;
    }

    const robotSelect = document.getElementById('robot-select');
    const selectedRobot = robotSelect ? robotSelect.value : 'robot_1';

    if (selectedRobot === 'all') {
        alert('⚠️ Please select a specific robot for sequences');
        return;
    }

    let totalDuration = 0;

    switch (sequenceType) {
        case 'dance':
            totalDuration = window.simulator.queueDanceSequence(selectedRobot);
            console.log(`💃 Started dance sequence (${Math.round(totalDuration / 60)} minutes)`);
            break;
        case 'combat':
            totalDuration = window.simulator.queueCombatSequence(selectedRobot);
            console.log(`🥋 Started combat sequence (${totalDuration} seconds)`);
            break;
        case 'exercise':
            totalDuration = window.simulator.queueExerciseSequence(selectedRobot);
            console.log(`💪 Started exercise sequence (${totalDuration} seconds)`);
            break;
        case 'movement':
            totalDuration = window.simulator.queueMovementSequence(selectedRobot);
            console.log(`🚶 Started movement sequence (${totalDuration} seconds)`);
            break;
        case 'all':
            totalDuration = window.simulator.demonstrateTimingSequence(selectedRobot);
            console.log(`🎭 Started complete demo (${Math.round(totalDuration / 60)} minutes)`);
            break;
        default:
            console.error('❌ Unknown sequence type:', sequenceType);
            return;
    }

    // Update UI to show sequence is running
    const lastAction = document.getElementById('last-action');
    if (lastAction) {
        lastAction.textContent = `${sequenceType.toUpperCase()} Sequence (${Math.round(totalDuration)}s)`;
    }

    // Update queue status periodically
    updateQueueStatus();
    const statusInterval = setInterval(() => {
        updateQueueStatus();
        if (!window.simulator.isProcessingQueue && window.simulator.actionQueue.length === 0) {
            clearInterval(statusInterval);
            console.log(`✅ ${sequenceType} sequence completed`);
        }
    }, 1000);
}

// Function to clear the action queue
function clearQueue() {
    if (window.simulator) {
        window.simulator.clearActionQueue();
        updateQueueStatus();
        console.log('🗑️ Action queue cleared');
    }
}

// Function to show current queue status
function showQueueStatus() {
    if (window.simulator) {
        const status = window.simulator.getQueueStatus();
        console.log('📋 Queue Status:', status);

        let message = `Queue Length: ${status.queueLength}\n`;
        message += `Is Processing: ${status.isProcessing}\n`;
        if (status.nextAction) {
            message += `Next Action: ${status.nextAction.action} for ${status.nextAction.robotId}`;
        } else {
            message += 'Next Action: None';
        }

        alert(message);
    }
}

// Function to update queue status display
function updateQueueStatus() {
    if (window.simulator) {
        const status = window.simulator.getQueueStatus();
        const queueStatusElement = document.getElementById('queue-status');
        const currentActionElement = document.getElementById('current-action');

        if (queueStatusElement) {
            if (status.queueLength > 0) {
                queueStatusElement.textContent = `${status.queueLength} actions pending`;
                queueStatusElement.style.color = '#4A90E2';
            } else {
                queueStatusElement.textContent = 'Empty';
                queueStatusElement.style.color = '#666';
            }
        }

        if (currentActionElement) {
            if (status.isProcessing && status.nextAction) {
                currentActionElement.textContent = `${status.nextAction.action} (${status.nextAction.robotId})`;
                currentActionElement.style.color = '#28a745';
            } else {
                currentActionElement.textContent = 'None';
                currentActionElement.style.color = '#666';
            }
        }
    }
}

// Update queue status every second
setInterval(updateQueueStatus, 1000);

// Update status periodically
setInterval(() => {
    if (window.simulator) {
        const sceneStatus = document.getElementById('scene-status');
        const robotsLoaded = document.getElementById('robots-loaded');
        const connectionDetail = document.getElementById('connection-status-detail');

        if (sceneStatus) {
            sceneStatus.textContent = window.simulator.scene3d ? 'Ready' : 'Loading...';
        }

        if (robotsLoaded) {
            robotsLoaded.textContent = `${window.simulator.robots.size}/6`;
        }

        if (connectionDetail) {
            connectionDetail.textContent = window.simulator.isConnected ? 'Connected to WebSocket' : 'Using Local Animations';
        }
    }
}, 1000);

// Show animation indicator when actions are triggered
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('action-btn') && e.target.dataset.action) {
        const action = e.target.dataset.action;
        const indicator = document.getElementById('animation-indicator');
        const isMovement = e.target.classList.contains('movement-btn');

        // Get action duration and show in indicator
        let duration = 2; // default
        if (window.simulator) {
            duration = window.simulator.getActionDuration(action);
        }

        if (indicator) {
            indicator.textContent = `${isMovement ? '🚶' : '🎭'} ${action.toUpperCase()} (${duration}s)`;
            indicator.classList.add('active');
            if (isMovement) {
                indicator.classList.add('movement');
            }

            // Keep indicator visible for the actual duration of the action
            setTimeout(() => {
                indicator.classList.remove('active', 'movement');
            }, duration * 1000);
        }

        // Log action timing
        console.log(`🎭 Action: ${action} - Duration: ${duration} seconds`);
    }
});

// Function to display action timing information
function showActionTimings() {
    const timings = {
        // Dance actions (long durations)
        'dance_two': 52,
        'dance_three': 70,
        'dance_four': 59,
        'dance_five': 59,
        'dance_six': 69,
        'dance_seven': 67,
        'dance_eight': 85,
        'dance_nine': 84,
        'dance_ten': 85,

        // Movement actions
        'stepping': 3,
        'twist': 4,
        'stand_up_back': 5,
        'stand_up_front': 5,
        'right_kick': 2,
        'left_kick': 2,
        'right_uppercut': 2,
        'left_uppercut': 2,
        'wing_chun': 2,
        'right_shot_fast': 4,
        'left_shot_fast': 4,
        'chest': 9,
        'squat_up': 6,
        'squat': 1,
        'bow': 4,
        'wave': 3.5,
        'turn_right': 4,
        'turn_left': 4,
        'sit_ups': 12,
        'right_move_fast': 3,
        'left_move_fast': 3,
        'back_fast': 4.5,
        'go_forward': 3.5,
        'push_ups': 9,
        'weightlifting': 9,
        'kung_fu': 2,

        // Additional backend actions
        'stand': 1,
        'stop': 3
    };

    console.log('⏱️ Action Timings (seconds):');
    console.table(timings);

    let message = 'Action Timings (seconds):\n\n';
    Object.entries(timings).forEach(([action, time]) => {
        message += `${action}: ${time}s\n`;
    });

    alert(message);
}

// Add timing info button to console
console.log('💡 Use showActionTimings() to see all action durations');
console.log('💡 Use runSequence("dance") to test long dance sequence');
console.log('💡 Use runSequence("combat") to test quick combat moves');
console.log('💡 Use clearQueue() to stop current sequence');
