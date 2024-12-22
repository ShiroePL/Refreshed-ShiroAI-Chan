import { RecognitionStates } from './states.js';
import { UIHandler } from './uiHandler.js';

export class RecognitionCore {
    constructor() {
        this.recognition = null;
        this.isRecognizing = false;
        this.noSpeechTimeout = null;
        this.retryCount = 0;
        this.maxRetries = 3;
    }

    setup(language, onStart, onEnd, onResult, onError) {
        this.cleanup();
        
        this.recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
        this.recognition.interimResults = true;
        this.recognition.continuous = true;
        this.recognition.lang = language;

        if (typeof this.recognition.maxSilenceTime !== 'undefined') {
            this.recognition.maxSilenceTime = 0;
        }

        this.recognition.onstart = () => {
            this.isRecognizing = true;
            if (onStart) onStart();
        };

        this.recognition.onend = () => {
            this.isRecognizing = false;
            if (onEnd) onEnd();
        };

        this.recognition.onresult = onResult;
        this.recognition.onerror = (error) => {
            if (this.noSpeechTimeout) {
                clearTimeout(this.noSpeechTimeout);
                this.noSpeechTimeout = null;
            }
            if (onError) onError(error);
        };

        this.recognition.onaudiostart = () => {
            if (this.noSpeechTimeout) {
                clearTimeout(this.noSpeechTimeout);
                this.noSpeechTimeout = null;
            }
        };
    }

    cleanup() {
        if (this.noSpeechTimeout) {
            clearTimeout(this.noSpeechTimeout);
            this.noSpeechTimeout = null;
        }

        if (this.recognition) {
            try {
                // Remove all event listeners first
                this.recognition.onresult = null;
                this.recognition.onend = null;
                this.recognition.onstart = null;
                this.recognition.onerror = null;
                this.recognition.onaudiostart = null;
                
                if (this.isRecognizing) {
                    this.recognition.stop();
                }
                
                // Properly dispose of the recognition object
                this.recognition.abort();
            } catch (e) {
                console.warn("Cleanup warning:", e);
            } finally {
                this.recognition = null;
                this.isRecognizing = false;
                this.retryCount = 0;
            }
        }
    }

    async start() {
        try {
            if (this.isRecognizing) {
                await new Promise((resolve) => {
                    const onEnd = () => {
                        this.recognition.onend = null;
                        this.cleanup();
                        resolve();
                    };
                    this.recognition.onend = onEnd;
                    this.recognition.stop();
                });
            }
            return this.startImmediate();
        } catch (error) {
            this.cleanup();
            throw error;
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