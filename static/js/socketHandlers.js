export class SocketHandler {
    constructor(socket) {
        this.socket = socket;
        this.currentAudio = null;
        this.audioQueue = [];
        this.isPlaying = false;
        this.voiceEnabled = true;
    }

    initialize() {
        this.setupResponseHandlers();
    }

    setupResponseHandlers() {
        this.socket.on('response', async (data) => {
            console.log('Received response:', data);
            
            // Update text response immediately
            document.getElementById('response').textContent = data.text || data.response || 'No response';
            
            // Handle audio if present and voice is enabled
            if (data.audio && this.voiceEnabled) {
                await this.playAudioResponse(data.audio);
            }
        });

        // Add handler for stop command
        this.socket.on('stop_audio', () => {
            this.stopCurrentAudio();
        });

        this.socket.on('error', (error) => {
            console.error('Socket error:', error);
            document.getElementById('response').textContent = 'Error: ' + (error.message || 'Unknown error');
        });
    }

    async playAudioResponse(audioData) {
        try {
            // Switch to trigger mode immediately when starting audio playback
            if (window.speechHandler) {
                window.speechHandler.switchToTriggerMode();
            }

            // Convert base64 to audio buffer
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const arrayBuffer = Uint8Array.from(atob(audioData), c => c.charCodeAt(0)).buffer;
            const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
            
            // Create and play audio source
            const source = audioContext.createBufferSource();
            source.buffer = audioBuffer;
            source.connect(audioContext.destination);
            
            this.currentAudio = source;
            this.isPlaying = true;
            
            // Play audio and handle completion
            source.start(0);
            source.onended = () => {
                this.isPlaying = false;
                this.currentAudio = null;
                this.socket.emit('audio_finished');
            };
        } catch (error) {
            console.error('Error playing audio:', error);
            this.isPlaying = false;
            this.currentAudio = null;
        }
    }

    stopCurrentAudio() {
        if (this.currentAudio) {
            try {
                this.currentAudio.stop();
                this.currentAudio.disconnect();
            } catch (e) {
                console.warn('Error stopping audio:', e);
            } finally {
                this.currentAudio = null;
                this.isPlaying = false;
                // Always emit audio_finished when stopping
                this.socket.emit('audio_finished');
            }
        }
    }

    isCurrentlyPlaying() {
        return this.isPlaying;
    }

    toggleVoice() {
        this.voiceEnabled = !this.voiceEnabled;
        const btn = document.getElementById('voiceToggleBtn');
        if (btn) {
            btn.innerHTML = this.voiceEnabled ? 
                '<i class="bi bi-volume-up-fill"></i> Voice On' : 
                '<i class="bi bi-volume-mute-fill"></i> Voice Off';
        }
    }
} 