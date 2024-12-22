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
        this.setupRecognition('en-US');
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
        console.log('Recognition ended, current state:', this.state);
        
        // Always restart recognition if we're in LISTENING_FOR_TRIGGER state
        if (this.state === RecognitionStates.LISTENING_FOR_TRIGGER) {
            setTimeout(() => {
                if (this.state === RecognitionStates.LISTENING_FOR_TRIGGER) {
                    this.startRecognition();
                }
            }, 100);
        }
    }

    handleError(event) {
        // Ignore abort errors as they're usually intentional
        if (event.error === 'aborted') {
            return;
        }

        if (event.error !== 'no-speech') {
            console.error("Recognition error:", event.error);
        }
        
        // Only attempt restart for no-speech errors during active listening
        if (event.error === 'no-speech' && 
            (this.state === RecognitionStates.LISTENING_FOR_TRIGGER || 
             this.socketHandler?.isCurrentlyPlaying())) {
            // Add delay before restart to prevent tight loops
            setTimeout(() => {
                if (this.state === RecognitionStates.LISTENING_FOR_TRIGGER) {
                    this.startRecognition();
                }
            }, 1000);
            return;
        }

        // For other errors, transition to error state briefly
        this.setState(RecognitionStates.ERROR);
        setTimeout(() => {
            if (this.state === RecognitionStates.ERROR) {
                if (this.previousState === RecognitionStates.LISTENING_FOR_TRIGGER) {
                    this.switchToTriggerMode();
                } else {
                    this.setState(RecognitionStates.IDLE);
                }
            }
        }, 2000);
    }

    handleResult(event) {
        let interimTranscript = '';
        let finalTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
                finalTranscript += transcript;
                if (finalTranscript.trim().length > 0) {
                    switch (this.state) {
                        case RecognitionStates.LISTENING_FOR_TRIGGER:
                            const wasTriggered = ModeHandlers.handleTriggerMode(
                                transcript, 
                                this.switchToCommandMode.bind(this)
                            );
                            if (!wasTriggered) {
                                // Check for stop command even in trigger mode
                                if (transcript.toLowerCase().includes('stop')) {
                                    if (this.socketHandler?.isCurrentlyPlaying()) {
                                        this.socketHandler.stopCurrentAudio();
                                        this.socket.emit('audio_finished');
                                    }
                                }
                                this.core.cleanup();
                                this.setupRecognition('en-US');
                                this.startRecognition();
                            }
                            break;
                        case RecognitionStates.LISTENING_FOR_COMMAND:
                        case RecognitionStates.PUSH_TO_TALK:
                            // Check for stop command first
                            if (transcript.toLowerCase().includes('stop')) {
                                if (this.socketHandler?.isCurrentlyPlaying()) {
                                    this.socketHandler.stopCurrentAudio();
                                    this.socket.emit('audio_finished');
                                    this.switchToTriggerMode();
                                    return;
                                }
                            }
                            // Send transcript directly to backend
                            this.socket.emit('transcript', { 
                                transcript: transcript.trim() 
                            });
                            break;
                    }
                }
            } else {
                interimTranscript += transcript;
            }
        }

        // Update UI with transcripts
        document.getElementById('interim').textContent = interimTranscript;
        if (finalTranscript) {
            document.getElementById('final').textContent = finalTranscript;
        }
    }

    switchToCommandMode(initialCommand, isDirectCommand = false) {
        this.core.cleanup();
        
        if (isDirectCommand) {
            if (initialCommand === 'shutdown') {
                this.socket.emit('stop_listening');
                this.setState(RecognitionStates.IDLE);
                return;
            }
            if (initialCommand === 'stop' && this.socketHandler?.isCurrentlyPlaying()) {
                this.socketHandler.stopCurrentAudio();
                this.switchToTriggerMode();
                return;
            }
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
        // Clean up existing recognition
        this.core.cleanup();
        // Setup new recognition
        this.setupRecognition('en-US');
        // Set state
        this.setState(RecognitionStates.LISTENING_FOR_TRIGGER);
        // Start new recognition
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