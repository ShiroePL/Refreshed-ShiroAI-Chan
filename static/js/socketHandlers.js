class SocketHandler {
    constructor(socket) {
        this.socket = socket;
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        this.currentSource = null;
        this.currentAudioBuffer = null;
        this.voiceEnabled = true;
        this.pendingVoiceDisable = false;
    }

    initialize() {
        this.socket.on('response', this.handleResponse.bind(this));
        this.socket.on('status_update', this.handleStatusUpdate.bind(this));
    }

    stopCurrentAudio() {
        if (this.currentSource) {
            this.currentSource.stop();
            this.currentSource = null;
            
            if (this.pendingVoiceDisable) {
                this.completeVoiceDisable();
            }
        }
    }

    completeVoiceDisable() {
        this.pendingVoiceDisable = false;
        this.voiceEnabled = false;
        const btn = document.getElementById('voiceToggleBtn');
        btn.innerHTML = '<i class="bi bi-volume-mute-fill"></i> Voice Off';
        btn.classList.remove('btn-success');
        btn.classList.add('btn-danger');
    }

    async handleResponse(data) {
        // Update text response
        document.getElementById('response').textContent = data.text;

        // Play audio if available and voice is enabled
        if (data.audio && this.voiceEnabled) {
            // Stop any currently playing audio first
            this.stopCurrentAudio();
            await this.playAudio(data.audio);
        }
    }

    async playAudio(base64Audio) {
        try {
            // Convert base64 to array buffer
            const audioData = atob(base64Audio);
            const arrayBuffer = new ArrayBuffer(audioData.length);
            const view = new Uint8Array(arrayBuffer);
            for (let i = 0; i < audioData.length; i++) {
                view[i] = audioData.charCodeAt(i);
            }

            // Decode audio data
            const audioBuffer = await this.audioContext.decodeAudioData(arrayBuffer);
            this.currentAudioBuffer = audioBuffer;
            
            // Create and play audio source
            const source = this.audioContext.createBufferSource();
            source.buffer = audioBuffer;
            source.connect(this.audioContext.destination);
            
            // Store reference to current source
            this.currentSource = source;
            
            // Handle audio end
            source.onended = () => {
                if (this.currentSource === source) {
                    this.currentSource = null;
                    if (this.pendingVoiceDisable) {
                        this.completeVoiceDisable();
                    }
                }
            };

            source.start(0);
        } catch (error) {
            console.error('Error playing audio:', error);
            this.currentSource = null;
            if (this.pendingVoiceDisable) {
                this.completeVoiceDisable();
            }
        }
    }

    handleStatusUpdate(data) {
        const statusElement = document.getElementById('listening-status');
        const listenBtn = document.getElementById('listenBtn');
        
        statusElement.textContent = data.listening ? 'Listening' : 'Not Listening';
        statusElement.className = data.listening ? 'status-active' : 'status-inactive';
        
        // Update button state to match status
        if (data.listening) {
            listenBtn.innerHTML = '<i class="bi bi-mic-mute-fill"></i> Stop Listening';
            listenBtn.classList.remove('btn-primary');
            listenBtn.classList.add('btn-danger');
        } else {
            listenBtn.innerHTML = '<i class="bi bi-mic-fill"></i> Start Listening';
            listenBtn.classList.remove('btn-danger');
            listenBtn.classList.add('btn-primary');
        }
    }

    toggleVoice() {
        if (this.voiceEnabled) {
            if (this.currentSource) {
                this.pendingVoiceDisable = true;
                const btn = document.getElementById('voiceToggleBtn');
                btn.innerHTML = '<i class="bi bi-volume-mute-fill"></i> Voice Off (After Current)';
                btn.classList.remove('btn-success');
                btn.classList.add('btn-danger');
            } else {
                this.completeVoiceDisable();
            }
        } else {
            this.pendingVoiceDisable = false;
            this.voiceEnabled = true;
            const btn = document.getElementById('voiceToggleBtn');
            btn.innerHTML = '<i class="bi bi-volume-up-fill"></i> Voice On';
            btn.classList.remove('btn-danger');
            btn.classList.add('btn-success');
        }
    }
} 