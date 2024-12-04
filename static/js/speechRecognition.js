class SpeechRecognitionHandler {
    constructor(socket) {
        this.recognition = null;
        this.isListening = false;
        this.isPushToTalk = false;
        this.socket = socket;
        this.socketHandler = null;
        this.initialize();
    }

    initialize() {
        if (!this.recognition) {
            this.recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
            this.recognition.interimResults = true;
            this.recognition.continuous = true;
            this.recognition.lang = 'en-US';

            this.recognition.onresult = this.handleResult.bind(this);
            this.recognition.onerror = this.handleError.bind(this);
            
            this.recognition.onend = () => {
                if (this.isPushToTalk) {
                    this.isPushToTalk = false;
                    document.getElementById('pushToTalkBtn').classList.remove('btn-danger');
                    document.getElementById('pushToTalkBtn').classList.add('btn-info');
                } else if (this.isListening) {
                    this.recognition.start();
                }
            };
        }
    }

    startPushToTalk() {
        if (this.isListening) {
            this.stop();
        }
        
        this.isPushToTalk = true;
        this.recognition.start();
        document.getElementById('pushToTalkBtn').classList.remove('btn-info');
        document.getElementById('pushToTalkBtn').classList.add('btn-danger');
    }

    stopPushToTalk() {
        if (this.isPushToTalk) {
            this.recognition.stop();
        }
    }

    start() {
        if (!this.isPushToTalk) {
            this.isListening = true;
            this.recognition.start();
        }
    }

    stop() {
        this.isListening = false;
        this.recognition.stop();
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
                if (finalTranscript.trim().length > 0) {
                    this.socket.emit('transcript', { transcript: transcript });
                }
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
} 