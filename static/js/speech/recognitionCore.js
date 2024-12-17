import { RecognitionStates } from './states.js';
import { UIHandler } from './uiHandler.js';

export class RecognitionCore {
    constructor() {
        this.recognition = null;
        this.isRecognizing = false;
    }

    setup(language, onStart, onEnd, onResult, onError) {
        this.cleanup();
        
        this.recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
        this.recognition.interimResults = true;
        this.recognition.continuous = true;
        this.recognition.lang = language;

        this.recognition.onstart = () => {
            this.isRecognizing = true;
            if (onStart) onStart();
        };

        this.recognition.onend = () => {
            this.isRecognizing = false;
            if (onEnd) onEnd();
        };

        this.recognition.onresult = onResult;
        this.recognition.onerror = onError;
    }

    cleanup() {
        if (this.recognition) {
            try {
                if (this.isRecognizing) {
                    this.recognition.stop();
                }
            } catch (e) {
                console.log('Cleanup stop error:', e);
            }
            this.recognition.onresult = null;
            this.recognition.onend = null;
            this.recognition.onstart = null;
            this.recognition.onerror = null;
            this.recognition = null;
        }
        this.isRecognizing = false;
    }

    start() {
        if (this.isRecognizing) {
            console.log('Recognition already active, stopping first...');
            return new Promise((resolve) => {
                const onEnd = () => {
                    this.recognition.onend = null;
                    this.startImmediate();
                    resolve();
                };
                this.recognition.onend = onEnd;
                this.recognition.stop();
            });
        } else {
            return this.startImmediate();
        }
    }

    startImmediate() {
        try {
            this.recognition.start();
            return Promise.resolve();
        } catch (error) {
            console.error("Error starting recognition:", error);
            throw error;
        }
    }

    stop() {
        try {
            if (this.isRecognizing) {
                this.recognition.stop();
            }
        } catch (error) {
            console.error("Error stopping recognition:", error);
        }
    }

    isActive() {
        return this.isRecognizing;
    }
} 