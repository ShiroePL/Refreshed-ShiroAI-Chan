import { SpeechRecognitionHandler } from './speechRecognition.js';
import { SocketHandler } from '../socketHandlers.js';

// Global variables
window.isPushToTalkPressed = false;
window.speechHandler = null;
window.socketHandler = null;
window.socket = null;
window.isPageVisible = true;
window.BRAIN_SERVICE_URL = 'http://127.0.0.1:8015';

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

    // Add reconnection handlers
    socket.on('reconnect', (attemptNumber) => {
        console.log('Reconnected on attempt:', attemptNumber);
        // Reinitialize handlers if needed
        if (window.speechHandler) {
            window.speechHandler.initialize();
        }
    });

    socket.on('reconnect_error', (error) => {
        console.log('Reconnection error:', error);
    });

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
document.addEventListener('visibilitychange', async () => {
    window.isPageVisible = document.visibilityState === 'visible';
    
    if (!window.isPageVisible) {
        // Only try wake lock if the API is available
        if ('wakeLock' in navigator) {
            try {
                // Store the wake lock instance
                window.wakeLock = await navigator.wakeLock.request('screen');
                
                // Release it when the page becomes visible again
                window.wakeLock.addEventListener('release', () => {
                    console.log('Wake Lock was released');
                });
            } catch (err) {
                // Log but don't throw - this is an expected error when page isn't visible
                console.log('Wake Lock error:', err.name, err.message);
            }
        }
    } else {
        // Release wake lock when page becomes visible
        if (window.wakeLock) {
            try {
                await window.wakeLock.release();
                window.wakeLock = null;
            } catch (err) {
                console.log('Error releasing wake lock:', err);
            }
        }
    }
});

// Keep alive functionality
setInterval(() => {
    if (!window.isPageVisible && window.socket && window.socket.connected) {
        window.socket.emit('keepalive');
    }
}, 30000);

// Initialize after DOM is loaded
document.addEventListener('DOMContentLoaded', initializeApp);