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
        // Add audio feedback element
        this.switchSound = new Audio('/static/sounds/switch.mp3');  // We'll create this file
        this.initialize();
    }

    setState(newState) {
        console.log(`State transition: ${this.state} -> ${newState}`);
        this.state = newState;
        this.updateUI();
    }

    initialize() {
        if (!this.recognition) {
            this.setupRecognition();
        }
    }

    setupRecognition(language = 'en-US') {
        // Stop existing recognition if it exists
        if (this.recognition) {
            this.recognition.stop();
        }

        this.recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
        this.recognition.interimResults = true;
        this.recognition.continuous = true;
        this.recognition.lang = language;

        // Re-attach all event handlers
        this.recognition.onstart = () => {
            console.log(`Recognition started (${language})`);
            if (this.state === SpeechRecognitionHandler.States.STARTING) {
                this.setState(this.pendingState || SpeechRecognitionHandler.States.LISTENING);
            }
        };

        this.recognition.onend = () => {
            console.log(`Recognition ended (${language})`);
            
            // Don't auto-restart if we're switching languages
            if (this.switching) {
                return;
            }

            switch (this.state) {
                case SpeechRecognitionHandler.States.PUSH_TO_TALK:
                    this.setState(SpeechRecognitionHandler.States.IDLE);
                    break;
                case SpeechRecognitionHandler.States.LISTENING:
                    // Auto-restart continuous listening
                    setTimeout(() => {
                        if (this.state === SpeechRecognitionHandler.States.LISTENING && !this.switching) {
                            this.startRecognition(SpeechRecognitionHandler.States.LISTENING);
                        }
                    }, 200);
                    break;
            }
        };

        this.recognition.onresult = this.handleResult.bind(this);
        this.recognition.onerror = this.handleError.bind(this);
    }

    handleError(event) {
        console.error("Recognition error:", event.error);
        this.setState(SpeechRecognitionHandler.States.ERROR);
        this.recognition.stop();
        setTimeout(() => {
            if (this.state === SpeechRecognitionHandler.States.ERROR) {
                this.setState(SpeechRecognitionHandler.States.IDLE);
            }
        }, 1000);
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
                    if (this.state === SpeechRecognitionHandler.States.LISTENING) {
                        const triggerWords = ['hi shiro', 'はい シロ', 'hi シロ', 'はいシロ', 'はいしろ', 'ハイシロ]'];
                        const lowerTranscript = transcript.toLowerCase();
                        
                        // Check if we're in English mode
                        if (this.recognition.lang === 'en-US') {
                            // Process the English command
                            this.socket.emit('transcript', { transcript: transcript });
                            // Switch back to Japanese mode after processing
                            this.switchBackToJapanese();
                        } else {
                            // Check for trigger word in Japanese mode
                            const triggered = triggerWords.some(trigger => 
                                lowerTranscript.includes(trigger.toLowerCase())
                            );

                            if (triggered) {
                                // Extract command after trigger word
                                const command = triggerWords.reduce((text, trigger) => {
                                    const parts = text.toLowerCase().split(trigger.toLowerCase());
                                    return parts.length > 1 ? parts.pop().trim() : text;
                                }, transcript);

                                // Switch to English for this command
                                this.switchToEnglish(command);
                            }
                        }
                    } else if (this.state === SpeechRecognitionHandler.States.PUSH_TO_TALK) {
                        this.socket.emit('transcript', { transcript: transcript });
                    }

                    if (transcript.toLowerCase().includes('stop')) {
                        this.stop();
                    }
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

    // Add method to play switch sound
    playSwitch() {
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            // Configure sound
            oscillator.type = 'sine';
            oscillator.frequency.setValueAtTime(1000, audioContext.currentTime); // Frequency in hertz
            gainNode.gain.setValueAtTime(0.1, audioContext.currentTime); // Volume
            
            // Start and stop the tone
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.15); // Duration in seconds
            
            // Fade out
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.15);
        } catch (e) {
            console.log('Audio feedback failed:', e);
        }
    }

    // Modify switchToEnglish to use the new sound
    switchToEnglish(command) {
        this.switching = true;
        this.recognition.stop();
        
        if (command && command.trim()) {
            this.socket.emit('transcript', { transcript: command });
        }

        setTimeout(() => {
            this.switching = false;
            this.setupRecognition('en-US');
            this.startRecognition(SpeechRecognitionHandler.States.LISTENING);
            // Play switch sound
            this.playSwitch();
            // Update UI
            const statusElement = document.getElementById('listening-status');
            statusElement.textContent = 'Listening in English...';
        }, 300);
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
            // Start with Japanese recognition for trigger word
            this.setupRecognition('ja-JP');
            this.socket.emit('start_listening');
            this.startRecognition(SpeechRecognitionHandler.States.LISTENING);
            // Update UI to show we're listening in Japanese
            const statusElement = document.getElementById('listening-status');
            statusElement.textContent = 'Listening for: "Hi Shiro" / "はい シロ"';
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
            this.setState(SpeechRecognitionHandler.States.IDLE);
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

    // Add method to switch back to Japanese mode
    switchBackToJapanese() {
        this.switching = true;
        this.recognition.stop();

        setTimeout(() => {
            this.switching = false;
            this.setupRecognition('ja-JP');
            this.startRecognition(SpeechRecognitionHandler.States.LISTENING);
            // Update UI
            const statusElement = document.getElementById('listening-status');
            statusElement.textContent = 'Listening for: "Hi Shiro" / "はい シロ"';
        }, 300);
    }
} 