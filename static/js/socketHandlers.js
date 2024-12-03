class SocketHandler {
    constructor(socket) {
        this.socket = socket;
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
    }

    initialize() {
        this.socket.on('response', this.handleResponse.bind(this));
        this.socket.on('status_update', this.handleStatusUpdate.bind(this));
    }

    async handleResponse(data) {
        // Update text response
        document.getElementById('response').textContent = data.text;

        // Play audio if available
        if (data.audio) {
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
            
            // Create and play audio source
            const source = this.audioContext.createBufferSource();
            source.buffer = audioBuffer;
            source.connect(this.audioContext.destination);
            source.start(0);
        } catch (error) {
            console.error('Error playing audio:', error);
        }
    }

    handleStatusUpdate(data) {
        const statusElement = document.getElementById('listening-status');
        statusElement.textContent = data.listening ? 'Listening' : 'Not Listening';
        statusElement.className = data.listening ? 'status-active' : 'status-inactive';
    }
} 