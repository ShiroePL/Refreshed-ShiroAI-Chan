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
        this.state = newState;
        UIHandler.updateStatus(newState);
    }

    setupRecognition(language) {
        this.core.setup(
            language,
            () => console.log(`Recognition started (${language})`),
            this.handleRecognitionEnd.bind(this),
            this.handleResult.bind(this),
            this.handleError.bind(this)
        );
    }

    handleRecognitionEnd() {
        console.log('Recognition ended');
        if (this.state === RecognitionStates.LISTENING_FOR_TRIGGER) {
            setTimeout(() => {
                if (this.state === RecognitionStates.LISTENING_FOR_TRIGGER) {
                    this.startRecognition();
                }
            }, 200);
        } else {
            this.setState(RecognitionStates.IDLE);
        }
    }

    handleError(event) {
        console.error("Recognition error:", event.error);
        this.core.cleanup();
        this.setState(RecognitionStates.ERROR);
        setTimeout(() => {
            if (this.state === RecognitionStates.ERROR) {
                this.setState(RecognitionStates.IDLE);
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
                    switch (this.state) {
                        case RecognitionStates.LISTENING_FOR_TRIGGER:
                            ModeHandlers.handleTriggerMode(transcript, this.switchToCommandMode.bind(this));
                            break;
                        case RecognitionStates.LISTENING_FOR_COMMAND:
                            ModeHandlers.handleCommandMode(transcript, this.socket, this.switchToTriggerMode.bind(this));
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

    switchToCommandMode(initialCommand) {
        this.core.cleanup();
        this.setupRecognition('en-US');
        this.setState(RecognitionStates.LISTENING_FOR_COMMAND);
        
        if (initialCommand && initialCommand.trim()) {
            this.socket.emit('transcript', { transcript: initialCommand });
        }

        AudioFeedback.playSwitch();
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

    startRecognition() {
        try {
            this.core.start();
        } catch (error) {
            console.error("Error starting recognition:", error);
            this.setState(RecognitionStates.ERROR);
        }
    }
} 