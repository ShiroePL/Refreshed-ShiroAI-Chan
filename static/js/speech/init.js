import { SpeechRecognitionHandler } from './speechRecognition.js';
import { SocketHandler } from '../socketHandlers.js';

// Global variables
window.isPushToTalkPressed = false;
window.speechHandler = null;
window.socketHandler = null;
window.socket = null;

// Initialize everything after DOM is loaded
async function initializeApp() {
    const socket = io({
        reconnectionAttempts: 5,  // Try to reconnect only 5 times
        reconnectionDelay: 1000,  // Start with 1 second delay
        reconnectionDelayMax: 5000,  // Maximum 5 seconds delay
        timeout: 5000,  // Connection timeout
        autoConnect: true  // Enable auto-connect
    });
    window.socket = socket;
    
    // Add reconnection error handler
    socket.on('reconnect_failed', () => {
        console.error('Failed to reconnect to server after maximum attempts');
        showConnectionError();
        socket.close();  // Explicitly close the socket
    });

    socket.on('connect_error', (error) => {
        console.error('Connection error:', error);
        showConnectionError();
    });

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
        showConnectionError();
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

    // Update response handlers
    socket.on('response', (data) => {
        // Update text response
        document.getElementById('response').textContent = data.text || data.response || 'No response';
        console.log('Received response:', data); // Add this for debugging
    });

    socket.on('error', (error) => {
        console.error('Socket error:', error);
        document.getElementById('response').textContent = 'Error: ' + (error.message || 'Unknown error');
    });

    // Add speaking status handler
    socket.on('speaking_status', (data) => {
        const statusElement = document.getElementById('listening-status');
        if (data.speaking) {
            statusElement.textContent = 'Assistant is speaking...';
            statusElement.className = 'status-active';
        }
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

// Add to initializeApp function
window.addEventListener('beforeunload', () => {
    if (window.socket) {
        window.socket.close();  // Explicitly close socket connection
    }
    if (window.socketHandler) {
        window.socketHandler.cleanup();
    }
    if (window.speechHandler) {
        window.speechHandler.core.cleanup();
    }
});

// Add error recovery
window.addEventListener('error', (event) => {
    console.error('Global error:', event.error);
    try {
        if (window.socketHandler) {
            window.socketHandler.cleanup();
            window.socketHandler.initialize().catch(console.error);
        }
        if (window.speechHandler) {
            window.speechHandler.core.cleanup();
            window.speechHandler.initialize();
        }
    } catch (e) {
        console.error('Error recovery failed:', e);
    }
});

// Add error display function
function showConnectionError() {
    const statusElement = document.getElementById('listening-status');
    if (statusElement) {
        statusElement.textContent = 'Server disconnected - Please refresh page';
        statusElement.className = 'status-inactive';
    }
}

// Add visibility change handler to manage connections
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        // Page is hidden (tab inactive)
        if (window.socket) {
            window.socket.close();
        }
    } else {
        // Page is visible again (tab active)
        if (window.socket && !window.socket.connected) {
            window.socket.connect();  // Reconnect only if needed
        }
    }
}); 