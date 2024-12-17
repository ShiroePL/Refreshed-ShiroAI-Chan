export class SocketHandler {
    constructor(socket) {
        this.socket = socket;
        this.audioContext = null;
        this.currentSource = null;
        this.voiceEnabled = true;
    }

    initialize() {
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        this.setupAudioHandlers();
    }

    setupAudioHandlers() {
        this.socket.on('audio', (audioChunk) => {
            if (!this.voiceEnabled) return;
            
            try {
                // Convert base64 to ArrayBuffer
                const base64 = audioChunk.replace('data:audio/wav;base64,', '');
                const binaryString = window.atob(base64);
                const bytes = new Uint8Array(binaryString.length);
                for (let i = 0; i < binaryString.length; i++) {
                    bytes[i] = binaryString.charCodeAt(i);
                }

                // Decode the WAV data
                this.audioContext.decodeAudioData(bytes.buffer, 
                    (decodedData) => {
                        // Create and play the audio
                        const source = this.audioContext.createBufferSource();
                        source.buffer = decodedData;
                        source.connect(this.audioContext.destination);
                        
                        this.currentSource = source;
                        source.start(0);
                        console.log('Playing audio chunk:', decodedData.length, 'samples');
                    },
                    (error) => {
                        console.error('Error decoding audio data:', error);
                    }
                );
            } catch (error) {
                console.error('Error processing audio:', error);
                console.error('Audio chunk type:', typeof audioChunk);
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
            } catch (e) {
                console.log('Error stopping audio:', e);
            }
            this.currentSource = null;
        }
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