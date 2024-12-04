const socket = io();
const socketHandler = new SocketHandler(socket);
const speechHandler = new SpeechRecognitionHandler(socket);

// Connect the handlers
speechHandler.socketHandler = socketHandler;

socketHandler.initialize();

function toggleListening() {
    const btn = document.getElementById('listenBtn');
    const isListening = btn.classList.contains('btn-danger');
    
    if (isListening) {
        // Stop listening
        speechHandler.stop();
        btn.innerHTML = '<i class="bi bi-mic-fill"></i> Start Listening';
        btn.classList.remove('btn-danger');
        btn.classList.add('btn-primary');
    } else {
        // Start listening
        socketHandler.stopCurrentAudio();
        speechHandler.start();
        btn.innerHTML = '<i class="bi bi-mic-mute-fill"></i> Stop Listening';
        btn.classList.remove('btn-primary');
        btn.classList.add('btn-danger');
    }
}

function toggleVoice() {
    socketHandler.toggleVoice();
}

function stopSpeaking() {
    socketHandler.stopCurrentAudio();
}

function startPushToTalk() {
    speechHandler.startPushToTalk();
}

function stopPushToTalk() {
    speechHandler.stopPushToTalk();
}

// Configuration for hotkeys
const PUSH_TO_TALK_KEY = '`';  // Backtick/tilde key

// Global flag to track push-to-talk state
let isPushToTalkPressed = false;

// Handle push-to-talk globally
document.addEventListener('keydown', (event) => {
    if (event.key === PUSH_TO_TALK_KEY && !isPushToTalkPressed) {
        isPushToTalkPressed = true;
        startPushToTalk();
    }
});

document.addEventListener('keyup', (event) => {
    if (event.key === PUSH_TO_TALK_KEY) {
        isPushToTalkPressed = false;
        stopPushToTalk();
    }
});

// Handle visibility change
document.addEventListener('visibilitychange', () => {
    // If push-to-talk was pressed before tab lost focus, maintain the state
    if (isPushToTalkPressed) {
        startPushToTalk();
    }
});

// Handle window focus/blur
window.addEventListener('blur', () => {
    // If push-to-talk was pressed before window lost focus, maintain the state
    if (isPushToTalkPressed) {
        startPushToTalk();
    }
});

// Cleanup on page unload
window.onbeforeunload = function() {
    isPushToTalkPressed = false;
    speechHandler.stop();
    socketHandler.stopCurrentAudio();
}; 