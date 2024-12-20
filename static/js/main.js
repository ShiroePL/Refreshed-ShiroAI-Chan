// Wait for initialization before setting up handlers
window.addEventListener('app-initialized', () => {
    // Setup button event listeners
    document.getElementById('listenBtn').addEventListener('click', () => {
        const btn = document.getElementById('listenBtn');
        const isListening = btn.classList.contains('btn-danger');
        
        if (isListening) {
            window.speechHandler.stop();
            updateListeningUI(false);
        } else {
            window.socketHandler.stopCurrentAudio();
            window.speechHandler.start();
            updateListeningUI(true);
        }
    });

    const pushToTalkBtn = document.getElementById('pushToTalkBtn');
    pushToTalkBtn.addEventListener('mousedown', () => {
        if (!window.isPushToTalkPressed) {
            window.isPushToTalkPressed = true;
            window.speechHandler.startPushToTalk();
        }
    });
    pushToTalkBtn.addEventListener('mouseup', () => {
        if (window.isPushToTalkPressed) {
            window.isPushToTalkPressed = false;
            window.speechHandler.stopPushToTalk();
        }
    });
    // Add touch events for mobile
    pushToTalkBtn.addEventListener('touchstart', (e) => {
        e.preventDefault(); // Prevent mouse events from firing
        if (!window.isPushToTalkPressed) {
            window.isPushToTalkPressed = true;
            window.speechHandler.startPushToTalk();
        }
    });
    pushToTalkBtn.addEventListener('touchend', (e) => {
        e.preventDefault(); // Prevent mouse events from firing
        if (window.isPushToTalkPressed) {
            window.isPushToTalkPressed = false;
            window.speechHandler.stopPushToTalk();
        }
    });

    document.getElementById('voiceToggleBtn').addEventListener('click', () => {
        window.socketHandler.toggleVoice();
    });

    document.getElementById('stopSpeakingBtn').addEventListener('click', () => {
        window.socketHandler.stopCurrentAudio();
        window.socket.emit('audio_finished');
    });

    // Helper function for UI updates
    function updateListeningUI(isListening) {
        const btn = document.getElementById('listenBtn');
        const statusElement = document.getElementById('listening-status');
        
        if (isListening) {
            btn.innerHTML = '<i class="bi bi-mic-mute-fill"></i> Stop Listening';
            btn.classList.remove('btn-primary');
            btn.classList.add('btn-danger');
        } else {
            btn.innerHTML = '<i class="bi bi-mic-fill"></i> Start Listening';
            btn.classList.remove('btn-danger');
            btn.classList.add('btn-primary');
        }
    }

    // Keyboard event listeners
    document.addEventListener('keydown', (event) => {
        if (event.key === '`') {  // Backtick/tilde key
            event.preventDefault();
            if (!window.isPushToTalkPressed) {
                window.isPushToTalkPressed = true;
                window.speechHandler.startPushToTalk();
            }
        }
    });

    document.addEventListener('keyup', (event) => {
        if (event.key === '`') {
            if (window.isPushToTalkPressed) {
                window.isPushToTalkPressed = false;
                window.speechHandler.stopPushToTalk();
            }
        }
    });

    // Add connection status to page title
    window.socket.on('connect', () => {
        document.title = 'Voice Assistant Interface';
    });

    window.socket.on('connect_error', () => {
        document.title = 'Voice Assistant Interface (Disconnected)';
    });
});

// Cleanup on page unload
window.onbeforeunload = function() {
    window.isPushToTalkPressed = false;
    if (window.speechHandler) window.speechHandler.stop();
    if (window.socketHandler) window.socketHandler.stopCurrentAudio();
};