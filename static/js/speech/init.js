import { SpeechRecognitionHandler } from './speechRecognition.js';
import { SocketHandler } from '../socketHandlers.js';

// Global variables
window.isPushToTalkPressed = false;
window.speechHandler = null;
window.socketHandler = null;
window.socket = null;
window.isPageVisible = true;

// Initialize everything after DOM is loaded
async function initializeApp() {
    const socket = io({
        reconnectionAttempts: 5,
        reconnectionDelay: 1000,
        reconnectionDelayMax: 5000,
        timeout: 5000,
        autoConnect: true
    });
    window.socket = socket;

    try {
        // Create and initialize handlers
        window.socketHandler = new SocketHandler(socket);
        window.speechHandler = new SpeechRecognitionHandler(socket);
        
        // Connect handlers
        window.speechHandler.socketHandler = window.socketHandler;
        
        // Initialize socket handler
        window.socketHandler.initialize();

        // Dispatch event when initialization is complete
        window.dispatchEvent(new Event('app-initialized'));
    } catch (error) {
        console.error('Initialization error:', error);
        window.socketHandler?.showConnectionError();
    }
}

// Page visibility and wake lock handling
document.addEventListener('visibilitychange', () => {
    window.isPageVisible = document.visibilityState === 'visible';
    
    if (!window.isPageVisible) {
        try {
            if ('wakeLock' in navigator) {
                navigator.wakeLock.request('screen').catch(console.error);
            }
        } catch (err) {
            console.warn('Wake Lock API not supported', err);
        }
    }
});

// Keep alive functionality
setInterval(() => {
    if (!window.isPageVisible && window.socket) {
        window.socket.emit('keepalive');
    }
}, 30000);

// Initialize after DOM is loaded
document.addEventListener('DOMContentLoaded', initializeApp);