class SpeechRecognitionHandler {
    constructor(socket) {
        this.recognition = null;
        this.isListening = false;
        this.isPushToTalk = false;
        this.socket = socket;
        this.socketHandler = null;
        this.isInitialized = false;
        this.initialize();
    }

    setupErrorRecovery() {
        // Handle cases where the recognition might stop unexpectedly
        setInterval(() => {
            // Only check if we're supposed to be listening
            if ((this.isListening || this.isPushToTalk) && 
                this.recognition && 
                this.isInitialized && 
                !this.recognition.starting) {
                    
                console.log("Recognition state:", {
                    isListening: this.isListening,
                    isPushToTalk: this.isPushToTalk,
                    isInitialized: this.isInitialized
                });

                // Try to restart only if really needed
                this.restartRecognition();
            }
        }, 2000);  // Increased interval to reduce frequency
    }

    restartRecognition() {
        if (this.recognition.starting) {
            return;
        }

        try {
            console.log("Attempting to restart recognition...");
            this.recognition.stop();
            
            // Short delay before starting again
            setTimeout(() => {
                if (this.isListening || this.isPushToTalk) {
                    this.recognition.start();
                }
            }, 200);
            
        } catch (error) {
            console.error("Error in restartRecognition:", error);
            this.resetState();
        }
    }

    resetState() {
        this.isListening = false;
        this.isPushToTalk = false;
        this.recognition.starting = false;
        this.updateUI();
    }

    updateUI() {
        // Update Push-to-Talk button
        const pushToTalkBtn = document.getElementById('pushToTalkBtn');
        if (this.isPushToTalk) {
            pushToTalkBtn.classList.remove('btn-info');
            pushToTalkBtn.classList.add('btn-danger');
        } else {
            pushToTalkBtn.classList.remove('btn-danger');
            pushToTalkBtn.classList.add('btn-info');
        }

        // Update status
        const statusElement = document.getElementById('listening-status');
        if (this.isListening || this.isPushToTalk) {
            statusElement.textContent = this.isPushToTalk ? 'Push-to-Talk Active' : 'Listening';
            statusElement.className = 'status-active';
        } else {
            statusElement.textContent = 'Not Listening';
            statusElement.className = 'status-inactive';
        }
    }

    initialize() {
        if (!this.recognition) {
            this.recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
            this.recognition.interimResults = true;
            this.recognition.continuous = true;
            this.recognition.lang = 'en-US';
            this.recognition.starting = false;

            this.recognition.onstart = () => {
                console.log("Recognition started");
                this.recognition.starting = false;
                this.isInitialized = true;
            };

            this.recognition.onend = () => {
                console.log("Recognition ended");
                this.recognition.starting = false;
                
                if (this.isPushToTalk) {
                    this.isPushToTalk = false;
                    this.updateUI();
                } else if (this.isListening) {
                    setTimeout(() => {
                        try {
                            this.recognition.start();
                        } catch (error) {
                            console.error("Error restarting after end:", error);
                            this.resetState();
                        }
                    }, 200);
                }
            };

            this.recognition.onresult = this.handleResult.bind(this);
            this.recognition.onerror = (event) => {
                console.error("Recognition error:", event.error);
                this.resetState();
            };
        }
    }

    startPushToTalk() {
        if (this.recognition.starting) {
            return;
        }

        try {
            // Stop continuous listening if active
            if (this.isListening) {
                this.stop();
            }

            this.isPushToTalk = true;
            this.recognition.starting = true;
            this.recognition.start();
            this.updateUI();
            
        } catch (error) {
            console.error("Error in startPushToTalk:", error);
            this.resetState();
        }
    }

    stopPushToTalk() {
        if (this.isPushToTalk) {
            this.isPushToTalk = false;
            try {
                this.recognition.stop();
            } catch (error) {
                console.error("Error stopping recognition:", error);
            }
            this.updateUI();
        }
    }

    start() {
        if (!this.isPushToTalk && !this.recognition.starting) {
            this.isListening = true;
            try {
                this.recognition.start();
                this.updateUI();
            } catch (error) {
                console.error("Error in start:", error);
                this.resetState();
            }
        }
    }

    stop() {
        this.isListening = false;
        try {
            this.recognition.stop();
        } catch (error) {
            console.error("Error in stop:", error);
        }
        this.updateUI();
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