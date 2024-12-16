import { SpeechRecognitionHandler } from './speechRecognition.js';
import { SocketHandler } from '../socketHandlers.js';

// Global variables
window.isPushToTalkPressed = false;
window.speechHandler = null;
window.socketHandler = null;
window.socket = null;

// Initialize everything after DOM is loaded
async function initializeApp() {
    const socket = io();
    window.socket = socket;
    
    try {
        // Create handlers
        window.socketHandler = new SocketHandler(socket);
        window.speechHandler = new SpeechRecognitionHandler(socket);
        
        // Connect handlers
        window.speechHandler.socketHandler = window.socketHandler;
        
        // Initialize socket handler
        window.socketHandler.initialize();

        // Setup socket listeners
        setupSocketListeners(socket);

        // Dispatch event when initialization is complete
        window.dispatchEvent(new Event('app-initialized'));
    } catch (error) {
        console.error('Initialization error:', error);
    }
}

function setupSocketListeners(socket) {
    socket.on('hotkey_push_to_talk_start', () => {
        if (window.startPushToTalk) {
            window.startPushToTalk();
        }
    });

    socket.on('hotkey_push_to_talk_stop', () => {
        if (window.stopPushToTalk) {
            window.stopPushToTalk();
        }
    });

    socket.on('status_update', (data) => {
        if (!data.isPushToTalk && window.updateListeningUI) {
            window.updateListeningUI(data.listening);
        }
    });

    socket.on('audio_finished', () => {
        if (window.speechHandler) {
            window.speechHandler.switchToTriggerMode();
        }
    });

    // Add response handler
    socket.on('response', (data) => {
        document.getElementById('response').textContent = data.response;
    });
}

// Initialize after DOM is loaded
document.addEventListener('DOMContentLoaded', initializeApp);

// Initialize audio context after user interaction
document.body.addEventListener('click', () => {
    if (window.socketHandler?.audioContext?.state === 'suspended') {
        window.socketHandler.audioContext.resume();
    }
}); 