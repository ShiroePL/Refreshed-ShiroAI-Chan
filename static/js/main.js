const socket = io();
const socketHandler = new SocketHandler(socket);
const speechHandler = new SpeechRecognitionHandler(socket);

// Connect the handlers
speechHandler.socketHandler = socketHandler;

socketHandler.initialize();

function startListening() {
    // Stop any currently playing audio when starting to listen
    socketHandler.stopCurrentAudio();
    speechHandler.start();
}

function stopListening() {
    speechHandler.stop();
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