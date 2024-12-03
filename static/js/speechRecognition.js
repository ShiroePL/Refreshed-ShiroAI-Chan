class SpeechRecognitionHandler {
    constructor(socket) {
        this.recognition = null;
        this.isListening = false;
        this.socket = socket;
        this.socketHandler = null;
    }

    initialize() {
        this.recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
        this.recognition.interimResults = true;
        this.recognition.continuous = true;
        this.recognition.lang = 'en-US';

        this.recognition.onresult = this.handleResult.bind(this);
        this.recognition.onerror = this.handleError.bind(this);
    }

    handleResult(event) {
        let interimTranscript = '';
        let finalTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
                if (this.socketHandler) {
                    this.socketHandler.stopCurrentAudio();
                }
                
                finalTranscript += transcript;
                this.socket.emit('transcript', { transcript: transcript });
            } else {
                interimTranscript += transcript;
            }
        }

        document.getElementById('interim').textContent = interimTranscript;
        if (finalTranscript) {
            document.getElementById('final').textContent = finalTranscript;
        }
    }

    handleError(event) {
        console.error('Speech recognition error:', event.error);
        this.stop();
    }

    start() {
        if (!this.recognition) {
            this.initialize();
        }
        this.recognition.start();
        this.isListening = true;
        this.socket.emit('start_listening');
    }

    stop() {
        if (this.recognition) {
            this.recognition.stop();
        }
        this.isListening = false;
        this.socket.emit('stop_listening');
    }
} 