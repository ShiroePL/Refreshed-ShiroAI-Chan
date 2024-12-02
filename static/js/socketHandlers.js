class SocketHandler {
    constructor(socket) {
        this.socket = socket;
    }

    initialize() {
        this.socket.on('response', this.handleResponse);
        this.socket.on('status_update', this.handleStatusUpdate);
    }

    handleResponse(data) {
        document.getElementById('response').textContent = data.response;
    }

    handleStatusUpdate(data) {
        const statusElement = document.getElementById('listening-status');
        statusElement.textContent = data.listening ? 'Listening' : 'Not Listening';
        statusElement.className = data.listening ? 'status-active' : 'status-inactive';
    }
} 