// Configuration for hotkeys
const PUSH_TO_TALK_KEY = '`';  // Backtick/tilde key

const socket = io();
const socketHandler = new SocketHandler(socket);
const speechHandler = new SpeechRecognitionHandler(socket);
let isPushToTalkPressed = false;

// Connect the handlers
speechHandler.socketHandler = socketHandler;

socketHandler.initialize();

// Initialize audio context after user interaction
function initializeAudioContext() {
    if (socketHandler.audioContext.state === 'suspended') {
        socketHandler.audioContext.resume();
    }
}

// Add click handler to body to initialize audio
document.body.addEventListener('click', initializeAudioContext);

function toggleListening() {
    const btn = document.getElementById('listenBtn');
    const statusElement = document.getElementById('listening-status');
    const isListening = btn.classList.contains('btn-danger');
    
    if (isListening) {
        // Stop listening
        speechHandler.stop();
        updateListeningUI(false);
    } else {
        // Start listening
        socketHandler.stopCurrentAudio();
        speechHandler.start();
        updateListeningUI(true);
    }
}

function updateListeningUI(isListening) {
    const btn = document.getElementById('listenBtn');
    const statusElement = document.getElementById('listening-status');
    
    if (isListening) {
        btn.innerHTML = '<i class="bi bi-mic-mute-fill"></i> Stop Listening';
        btn.classList.remove('btn-primary');
        btn.classList.add('btn-danger');
        statusElement.textContent = 'Listening';
        statusElement.className = 'status-active';
    } else {
        btn.innerHTML = '<i class="bi bi-mic-fill"></i> Start Listening';
        btn.classList.remove('btn-danger');
        btn.classList.add('btn-primary');
        statusElement.textContent = 'Not Listening';
        statusElement.className = 'status-inactive';
    }
}

function toggleVoice() {
    socketHandler.toggleVoice();
}

function stopSpeaking() {
    socketHandler.stopCurrentAudio();
    // Emit audio finished event to ensure server state is updated
    socket.emit('audio_finished');
}

function startPushToTalk() {
    if (!isPushToTalkPressed) {
        isPushToTalkPressed = true;
        speechHandler.startPushToTalk();
    }
}

function stopPushToTalk() {
    if (isPushToTalkPressed) {
        isPushToTalkPressed = false;
        speechHandler.stopPushToTalk();
    }
}

// Listen for hotkey events from Python
socket.on('hotkey_push_to_talk_start', () => {
    startPushToTalk();
});

socket.on('hotkey_push_to_talk_stop', () => {
    stopPushToTalk();
});

// Browser keyboard events (only when focused)
document.addEventListener('keydown', (event) => {
    if (event.key === PUSH_TO_TALK_KEY) {
        event.preventDefault();
        startPushToTalk();
    }
});

document.addEventListener('keyup', (event) => {
    if (event.key === PUSH_TO_TALK_KEY) {
        stopPushToTalk();
    }
});

// Cleanup on page unload
window.onbeforeunload = function() {
    isPushToTalkPressed = false;
    speechHandler.stop();
    socketHandler.stopCurrentAudio();
};

// Update the socket handler to use the new UI update function
socket.on('status_update', (data) => {
    if (!data.isPushToTalk) {
        updateListeningUI(data.listening);
    }
}); 