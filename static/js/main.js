const socket = io();
const socketHandler = new SocketHandler(socket);
const speechHandler = new SpeechRecognitionHandler(socket);

// Connect the handlers
speechHandler.socketHandler = socketHandler;

socketHandler.initialize();

function startListening() {
    speechHandler.start();
}

function stopListening() {
    speechHandler.stop();
}

window.onbeforeunload = function() {
    speechHandler.stop();
    if (socketHandler.currentSource) {
        socketHandler.currentSource.stop();
    }
}; 