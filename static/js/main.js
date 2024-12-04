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

// Add keyboard shortcut to stop audio (optional)
document.addEventListener('keydown', (event) => {
    if (event.code === 'Escape') {
        socketHandler.stopCurrentAudio();
    }
});

window.onbeforeunload = function() {
    speechHandler.stop();
    socketHandler.stopCurrentAudio();
}; 