class SpeechRecognitionHandler {
    static States = {
        IDLE: 'IDLE',
        LISTENING: 'LISTENING',
        PUSH_TO_TALK: 'PUSH_TO_TALK',
        ERROR: 'ERROR',
        STARTING: 'STARTING'  // Added to handle initialization state
    };

    constructor(socket) {
        this.state = SpeechRecognitionHandler.States.IDLE;
        this.recognition = null;
        this.socket = socket;
        this.socketHandler = null;
        this.initialize();
    }

    setState(newState) {
        console.log(`State transition: ${this.state} -> ${newState}`);
        this.state = newState;
        this.updateUI();
    }

    initialize() {
        if (!this.recognition) {
            this.recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
            this.recognition.interimResults = true;
            this.recognition.continuous = true;
            this.recognition.lang = 'en-US';

            this.recognition.onstart = () => {
                console.log("Recognition started");
                if (this.state === SpeechRecognitionHandler.States.STARTING) {
                    this.setState(this.pendingState || SpeechRecognitionHandler.States.LISTENING);
                }
            };

            this.recognition.onend = () => {
                console.log("Recognition ended");
                
                switch (this.state) {
                    case SpeechRecognitionHandler.States.PUSH_TO_TALK:
                        this.setState(SpeechRecognitionHandler.States.IDLE);
                        break;
                    case SpeechRecognitionHandler.States.LISTENING:
                        // Auto-restart continuous listening
                        setTimeout(() => {
                            if (this.state === SpeechRecognitionHandler.States.LISTENING) {
                                this.startRecognition(SpeechRecognitionHandler.States.LISTENING);
                            }
                        }, 200);
                        break;
                }
            };

            this.recognition.onresult = this.handleResult.bind(this);
            
            this.recognition.onerror = (event) => {
                console.error("Recognition error:", event.error);
                this.setState(SpeechRecognitionHandler.States.ERROR);
                this.recognition.stop();
                setTimeout(() => {
                    if (this.state === SpeechRecognitionHandler.States.ERROR) {
                        this.setState(SpeechRecognitionHandler.States.IDLE);
                    }
                }, 1000);
            };
        }
    }

    startRecognition(targetState) {
        try {
            this.pendingState = targetState;
            this.setState(SpeechRecognitionHandler.States.STARTING);
            this.recognition.start();
        } catch (error) {
            console.error("Error starting recognition:", error);
            this.setState(SpeechRecognitionHandler.States.ERROR);
        }
    }

    start() {
        if (this.state === SpeechRecognitionHandler.States.IDLE) {
            this.socket.emit('start_listening');
            this.startRecognition(SpeechRecognitionHandler.States.LISTENING);
        }
    }

    stop() {
        if (this.state !== SpeechRecognitionHandler.States.IDLE) {
            this.socket.emit('stop_listening');
            try {
                this.recognition.stop();
                this.setState(SpeechRecognitionHandler.States.IDLE);
            } catch (error) {
                console.error("Error stopping recognition:", error);
                this.setState(SpeechRecognitionHandler.States.ERROR);
            }
        }
    }

    startPushToTalk() {
        if (this.state !== SpeechRecognitionHandler.States.PUSH_TO_TALK) {
            this.state = SpeechRecognitionHandler.States.PUSH_TO_TALK;
            this.updateUI();
            // Start recognition
            this.recognition.start();
            // Emit push-to-talk specific event
            this.socket.emit('push_to_talk_start');
        }
    }

    stopPushToTalk() {
        if (this.state === SpeechRecognitionHandler.States.PUSH_TO_TALK) {
            this.recognition.stop();
            this.state = SpeechRecognitionHandler.States.IDLE;
            this.updateUI();
            // Emit push-to-talk specific event
            this.socket.emit('push_to_talk_stop');
        }
    }

    updateUI() {
        // Update Push-to-Talk button
        const pushToTalkBtn = document.getElementById('pushToTalkBtn');
        const isPushToTalk = this.state === SpeechRecognitionHandler.States.PUSH_TO_TALK;
        pushToTalkBtn.classList.toggle('btn-danger', isPushToTalk);
        pushToTalkBtn.classList.toggle('btn-info', !isPushToTalk);

        // Update status text and class
        const statusElement = document.getElementById('listening-status');
        switch (this.state) {
            case SpeechRecognitionHandler.States.IDLE:
                statusElement.textContent = 'Not Listening';
                statusElement.className = 'status-inactive';
                break;
            case SpeechRecognitionHandler.States.LISTENING:
                statusElement.textContent = 'Listening';
                statusElement.className = 'status-active';
                break;
            case SpeechRecognitionHandler.States.PUSH_TO_TALK:
                statusElement.textContent = 'Push-to-Talk Active';
                statusElement.className = 'status-active';
                break;
            case SpeechRecognitionHandler.States.ERROR:
                statusElement.textContent = 'Error - Retrying...';
                statusElement.className = 'status-inactive';
                break;
            case SpeechRecognitionHandler.States.STARTING:
                statusElement.textContent = 'Starting...';
                statusElement.className = 'status-active';
                break;
        }
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
} 