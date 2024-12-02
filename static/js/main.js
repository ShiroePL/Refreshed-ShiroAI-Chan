const socket = io();
const speechHandler = new SpeechRecognitionHandler(socket);
const socketHandler = new SocketHandler(socket);

socketHandler.initialize();

function startListening() {
    speechHandler.start();
}

function stopListening() {
    speechHandler.stop();
}

window.onbeforeunload = function() {
    speechHandler.stop();
}; 