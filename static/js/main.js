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

    document.getElementById('text-mode-check').addEventListener('change', (e) => {
        const textContainer = document.getElementById('text-input-container');
        textContainer.style.display = e.target.checked ? 'block' : 'none';
        
        // Disable voice buttons when in text mode
        const voiceButtons = [
            'listenBtn',
            'pushToTalkBtn',
            'voiceToggleBtn',
            'stopSpeakingBtn'
        ];
        
        voiceButtons.forEach(id => {
            const btn = document.getElementById(id);
            btn.disabled = e.target.checked;
        });

        // Stop speech recognition if it's running when switching to text mode
        if (e.target.checked) {
            if (window.speechHandler) {
                window.speechHandler.stop();
                window.socket.emit('text_mode_start');
            }
            updateListeningUI(false);
        } else {
            window.socket.emit('text_mode_end');
        }
    });

    // Add text input handling
    document.getElementById('send-text-btn').addEventListener('click', sendTextMessage);
    document.getElementById('text-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendTextMessage();
        }
    });

    function sendTextMessage() {
        const textInput = document.getElementById('text-input');
        const message = textInput.value.trim();
        
        if (message) {
            // Update the transcript display
            document.getElementById('final').textContent = message;
            
            // Send to backend using the same socket event as voice
            window.socket.emit('transcript', { 
                transcript: message,
                skip_vtube: document.getElementById('skip-vtube-check').checked
            });
            
            // Clear the input
            textInput.value = '';
        }
    }
});

// Cleanup on page unload
window.onbeforeunload = function() {
    window.isPushToTalkPressed = false;
    if (window.speechHandler) window.speechHandler.stop();
    if (window.socketHandler) window.socketHandler.stopCurrentAudio();
};