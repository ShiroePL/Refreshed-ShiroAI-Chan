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
            
            const audioData = new Float32Array(audioChunk);
            const buffer = this.audioContext.createBuffer(1, audioData.length, 24000);
            buffer.getChannelData(0).set(audioData);
            
            const source = this.audioContext.createBufferSource();
            source.buffer = buffer;
            source.connect(this.audioContext.destination);
            
            this.currentSource = source;
            source.start(0);
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
        }
    }
} 