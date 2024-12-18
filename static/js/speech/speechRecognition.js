import { RecognitionStates } from './states.js';
import { UIHandler } from './uiHandler.js';
import { AudioFeedback } from './audioFeedback.js';
import { RecognitionCore } from './recognitionCore.js';
import { ModeHandlers } from './modeHandlers.js';

export class SpeechRecognitionHandler {
    constructor(socket) {
        this.state = RecognitionStates.IDLE;
        this.socket = socket;
        this.socketHandler = null;
        this.core = new RecognitionCore();
        this.initialize();
    }

    initialize() {
        this.setupRecognition('ja-JP');
    }

    setState(newState) {
        console.log(`State transition: ${this.state} -> ${newState}`);
        this.previousState = this.state;
        this.state = newState;
        UIHandler.updateStatus(newState);
        
        // Emit state change to backend for overlay updates
        if (this.socket) {
            this.socket.emit('state_change', { state: newState });
        }
    }

    setupRecognition(language) {
        this.core.setup(
            language,
            () => {
                if (this.state === RecognitionStates.IDLE || !this.state) {
                    console.log(`Recognition started (${language})`);
                }
            },
            this.handleRecognitionEnd.bind(this),
            this.handleResult.bind(this),
            this.handleError.bind(this)
        );
    }

    handleRecognitionEnd() {
        if (this.state !== RecognitionStates.LISTENING_FOR_TRIGGER) {
            console.log('Recognition ended');
        }
        
        if (this.state === RecognitionStates.LISTENING_FOR_TRIGGER) {
            setTimeout(() => {
                if (this.state === RecognitionStates.LISTENING_FOR_TRIGGER) {
                    this.startRecognition();
                }
            }, 100);
        } else {
            this.setState(RecognitionStates.IDLE);
        }
    }

    handleError(event) {
        if (event.error !== 'no-speech') {
            console.error("Recognition error:", event.error);
        }
        
        if (event.error === 'no-speech' && 
            (this.state === RecognitionStates.LISTENING_FOR_TRIGGER || this.socketHandler?.isCurrentlyPlaying())) {
            this.core.cleanup();
            this.setupRecognition('ja-JP');
            this.startRecognition();
            return;
        }

        this.core.cleanup();
        this.setState(RecognitionStates.ERROR);
        setTimeout(() => {
            if (this.state === RecognitionStates.ERROR) {
                if (this.previousState === RecognitionStates.LISTENING_FOR_TRIGGER) {
                    this.switchToTriggerMode();
                } else {
                    this.setState(RecognitionStates.IDLE);
                }
            }
        }, 1000);
    }

    handleResult(event) {
        let interimTranscript = '';
        let finalTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
                // Check for stop command first
                if (this.socketHandler) {
                    const stopWords = ['stop', 'ストップ', 'すとっぷ', 'とめて', 'やめて'];
                    const isStopCommand = stopWords.some(word => 
                        transcript.toLowerCase().includes(word.toLowerCase())
                    );

                    if (this.socketHandler.isCurrentlyPlaying() && isStopCommand) {
                        this.socketHandler.stopCurrentAudio();
                        this.switchToTriggerMode();
                        return;
                    }
                }
                
                finalTranscript += transcript;
                if (finalTranscript.trim().length > 0) {
                    switch (this.state) {
                        case RecognitionStates.LISTENING_FOR_TRIGGER:
                            const wasTriggered = ModeHandlers.handleTriggerMode(
                                transcript, 
                                this.switchToCommandMode.bind(this)
                            );
                            if (!wasTriggered) {
                                this.core.cleanup();
                                this.setupRecognition('ja-JP');
                                this.startRecognition();
                            }
                            break;
                        case RecognitionStates.LISTENING_FOR_COMMAND:
                            if (transcript === 'shutdown') {
                                this.core.cleanup();
                                this.setState(RecognitionStates.IDLE);
                                return;
                            }
                            ModeHandlers.handleCommandMode(
                                transcript, 
                                this.socket, 
                                this.switchToTriggerMode.bind(this)
                            );
                            break;
                        case RecognitionStates.PUSH_TO_TALK:
                            ModeHandlers.handlePushToTalk(transcript, this.socket);
                            break;
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

    switchToCommandMode(initialCommand, isDirectShutdown = false) {
        this.core.cleanup();
        
        if (isDirectShutdown) {
            // For direct shutdown, skip command mode entirely
            this.socket.emit('stop_listening');
            this.setState(RecognitionStates.IDLE);
            return;
        }

        this.setupRecognition('en-US');
        this.setState(RecognitionStates.LISTENING_FOR_COMMAND);
        
        AudioFeedback.playSwitch();
        
        if (initialCommand && initialCommand.trim()) {
            this.socket.emit('transcript', { transcript: initialCommand });
        }

        this.startRecognition();
    }

    switchToTriggerMode() {
        this.core.cleanup();
        this.setupRecognition('ja-JP');
        this.setState(RecognitionStates.LISTENING_FOR_TRIGGER);
        this.startRecognition();
    }

    startPushToTalk() {
        this.core.cleanup();
        this.setupRecognition('en-US');
        this.setState(RecognitionStates.PUSH_TO_TALK);
        this.startRecognition();
        this.socket.emit('push_to_talk_start');
    }

    stopPushToTalk() {
        if (this.state === RecognitionStates.PUSH_TO_TALK) {
            this.core.cleanup();
            this.setState(RecognitionStates.IDLE);
            this.socket.emit('push_to_talk_stop');
        }
    }

    start() {
        if (this.state === RecognitionStates.IDLE) {
            this.switchToTriggerMode();
            this.socket.emit('start_listening');
        }
    }

    stop() {
        this.core.cleanup();
        this.setState(RecognitionStates.IDLE);
        this.socket.emit('stop_listening');
    }

    async startRecognition() {
        try {
            await this.core.start();
        } catch (error) {
            console.error("Error starting recognition:", error);
            this.setState(RecognitionStates.ERROR);
        }
    }

    shutdown() {
        this.core.cleanup();
        this.setState(RecognitionStates.IDLE);
        // Clear any displayed transcripts
        document.getElementById('interim').textContent = '';
        document.getElementById('final').textContent = '';
        // Don't try to restart recognition
        this.state = RecognitionStates.IDLE;
        // Update the button UI
        const btn = document.getElementById('listenBtn');
        if (btn) {
            btn.innerHTML = '<i class="bi bi-mic-fill"></i> Start Listening';
            btn.classList.remove('btn-danger');
            btn.classList.add('btn-primary');
        }
    }
} 