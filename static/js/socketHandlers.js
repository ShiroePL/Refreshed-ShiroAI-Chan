export class SocketHandler {
    constructor(socket) {
        this.socket = socket;
        this.audioContext = null;
        this.currentSource = null;
        this.voiceEnabled = true;
        this.isPlaying = false;
    }

    initialize() {
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        this.setupAudioHandlers();
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
                        const source = this.audioContext.createBufferSource();
                        source.buffer = decodedData;
                        source.connect(this.audioContext.destination);
                        
                        this.currentSource = source;
                        this.isPlaying = true;

                        // Add onended handler
                        source.onended = () => {
                            this.isPlaying = false;
                            this.currentSource = null;
                            this.socket.emit('audio_finished');
                            console.log('Audio playback finished naturally');
                        };

                        source.start(0);
                        console.log('Started playing audio chunk:', decodedData.length, 'samples');
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
    }

    stopCurrentAudio() {
        if (this.currentSource) {
            try {
                this.currentSource.stop();
                this.isPlaying = false;
                this.currentSource = null;
                this.socket.emit('audio_finished');
            } catch (e) {
                console.log('Error stopping audio:', e);
            }
        }
    }

    isCurrentlyPlaying() {
        return this.isPlaying;
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