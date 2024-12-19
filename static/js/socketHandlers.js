export class SocketHandler {
    constructor(socket) {
        this.socket = socket;
        this.audioContext = null;
        this.currentSource = null;
        this.voiceEnabled = true;
        this.isPlaying = false;
        this.audioQueue = [];
        this.isProcessingQueue = false;
    }

    async initialize() {
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            await this.audioContext.resume();
            this.setupAudioHandlers();
        } catch (error) {
            console.error("Failed to initialize audio context:", error);
            throw error;
        }
    }

    cleanup() {
        this.stopCurrentAudio();
        this.audioQueue = [];
        this.isProcessingQueue = false;
        
        if (this.audioContext) {
            this.audioContext.close().catch(console.error);
            this.audioContext = null;
        }
    }

    async processAudioQueue() {
        if (this.isProcessingQueue || this.audioQueue.length === 0) return;
        
        this.isProcessingQueue = true;
        
        try {
            while (this.audioQueue.length > 0) {
                const audioChunk = this.audioQueue.shift();
                await this.playAudioChunk(audioChunk);
            }
        } catch (error) {
            console.error("Error processing audio queue:", error);
        } finally {
            this.isProcessingQueue = false;
        }
    }

    async playAudioChunk(audioChunk) {
        if (!this.voiceEnabled || !this.audioContext) return;

        try {
            const base64 = audioChunk.replace('data:audio/wav;base64,', '');
            const binaryString = window.atob(base64);
            const bytes = new Uint8Array(binaryString.length);
            for (let i = 0; i < binaryString.length; i++) {
                bytes[i] = binaryString.charCodeAt(i);
            }

            const audioBuffer = await this.audioContext.decodeAudioData(bytes.buffer);
            const source = this.audioContext.createBufferSource();
            source.buffer = audioBuffer;
            source.connect(this.audioContext.destination);
            
            return new Promise((resolve, reject) => {
                this.currentSource = source;
                this.isPlaying = true;

                source.onended = () => {
                    this.isPlaying = false;
                    this.currentSource = null;
                    this.socket.emit('audio_finished');
                    resolve();
                };

                source.start(0);
            });
        } catch (error) {
            this.isPlaying = false;
            this.currentSource = null;
            throw error;
        }
    }

    stopCurrentAudio() {
        console.log('Attempting to stop audio...');
        if (this.currentSource) {
            try {
                this.currentSource.stop();
                this.currentSource.disconnect();
            } catch (e) {
                console.warn("Error stopping audio:", e);
            } finally {
                // Always clean up and emit, even if stop fails
                this.currentSource = null;
                this.isPlaying = false;
                console.log('Audio stopped, emitting audio_finished');
                this.socket.emit('audio_finished');
            }
        }
    }

    setupAudioHandlers() {
        this.socket.on('audio', (audioChunk) => {
            if (!this.voiceEnabled) return;
            
            try {
                const base64 = audioChunk.replace('data:audio/wav;base64,', '');
                const binaryString = window.atob(base64);
                const bytes = new Uint8Array(binaryString.length);
                for (let i = 0; i < binaryString.length; i++) {
                    bytes[i] = binaryString.charCodeAt(i);
                }

                this.audioContext.decodeAudioData(bytes.buffer, 
                    (decodedData) => {
                        console.log('Starting audio playback...');
                        const source = this.audioContext.createBufferSource();
                        source.buffer = decodedData;
                        source.connect(this.audioContext.destination);
                        
                        this.currentSource = source;
                        this.isPlaying = true;
                        console.log('Audio state set - isPlaying:', this.isPlaying);

                        source.onended = () => {
                            console.log('Audio ended naturally');
                            this.isPlaying = false;
                            this.currentSource = null;
                            this.socket.emit('audio_finished');
                        };

                        source.start(0);
                    },
                    (error) => {
                        console.error('Error decoding audio data:', error);
                        this.isPlaying = false;
                    }
                );
            } catch (error) {
                console.error('Error processing audio:', error);
                this.isPlaying = false;
            }
        });

        // Add handler for the response that includes audio
        this.socket.on('response', (data) => {
            if (data.audio && this.voiceEnabled) {
                // Emit the audio data to be played
                this.socket.emit('audio', data.audio);
            }
        });

        // Add handler for audio errors
        this.socket.on('audio_error', (error) => {
            console.error('Audio streaming error:', error);
        });

        // Add handler for shutdown completion
        this.socket.on('shutdown_complete', () => {
            if (window.speechHandler) {
                window.speechHandler.shutdown();
            }
        });
    }

    isCurrentlyPlaying() {
        console.log('Checking if playing:', this.isPlaying, 'Current source:', !!this.currentSource);
        return this.isPlaying && this.currentSource !== null;
    }

    toggleVoice() {
        this.voiceEnabled = !this.voiceEnabled;
        const btn = document.getElementById('voiceToggleBtn');
        if (this.voiceEnabled) {
            btn.innerHTML = '<i class="bi bi-volume-up-fill"></i> Voice On';
            btn.classList.remove('btn-danger');
            btn.classList.add('btn-success');
        } else {
            btn.innerHTML = '<i class="bi bi-volume-mute-fill"></i> Voice Off';
            btn.classList.remove('btn-success');
            btn.classList.add('btn-danger');
            this.stopCurrentAudio(); // Stop any playing audio when voice is disabled
        }
    }
} 