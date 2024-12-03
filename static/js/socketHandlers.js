class SocketHandler {
    constructor(socket) {
        this.socket = socket;
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        this.currentSource = null;
        this.currentAudioBuffer = null;
    }

    initialize() {
        this.socket.on('response', this.handleResponse.bind(this));
        this.socket.on('status_update', this.handleStatusUpdate.bind(this));
    }

    stopCurrentAudio() {
        if (this.currentSource) {
            this.currentSource.stop();
            this.currentSource = null;
        }
    }

    async handleResponse(data) {
        // Update text response
        document.getElementById('response').textContent = data.text;

        // Play audio if available
        if (data.audio) {
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
            
            // Remove reference when playback ends naturally
            source.onended = () => {
                if (this.currentSource === source) {
                    this.currentSource = null;
                }
            };

            source.start(0);
        } catch (error) {
            console.error('Error playing audio:', error);
            this.currentSource = null;
        }
    }

    handleStatusUpdate(data) {
        const statusElement = document.getElementById('listening-status');
        statusElement.textContent = data.listening ? 'Listening' : 'Not Listening';
        statusElement.className = data.listening ? 'status-active' : 'status-inactive';
    }
} 