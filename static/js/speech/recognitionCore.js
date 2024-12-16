import { RecognitionStates } from './states.js';
import { UIHandler } from './uiHandler.js';

export class RecognitionCore {
    constructor() {
        this.recognition = null;
    }

    setup(language, onStart, onEnd, onResult, onError) {
        this.cleanup();
        
        this.recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
        this.recognition.interimResults = true;
        this.recognition.continuous = true;
        this.recognition.lang = language;

        this.recognition.onstart = onStart;
        this.recognition.onend = onEnd;
        this.recognition.onresult = onResult;
        this.recognition.onerror = onError;
    }

    cleanup() {
        if (this.recognition) {
            try {
                this.recognition.stop();
            } catch (e) {
                console.log('Cleanup stop error:', e);
            }
            this.recognition.onresult = null;
            this.recognition.onend = null;
            this.recognition.onstart = null;
            this.recognition.onerror = null;
            this.recognition = null;
        }
    }

    start() {
        try {
            this.recognition.start();
        } catch (error) {
            console.error("Error starting recognition:", error);
            throw error;
        }
    }

    stop() {
        try {
            this.recognition.stop();
        } catch (error) {
            console.error("Error stopping recognition:", error);
        }
    }
} 