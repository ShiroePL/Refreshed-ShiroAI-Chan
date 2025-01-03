export class SocketHandler {
    constructor(socket) {
        this.socket = socket;
        this.currentAudio = null;
        this.audioQueue = [];
        this.responseQueue = [];
        this.isPlaying = false;
        this.voiceEnabled = true;
        this.processingCount = 0;
        this.setupConnectionHandlers();
    }

    setupConnectionHandlers() {
        // Connection error handling
        this.socket.on('reconnect_failed', () => {
            console.error('Failed to reconnect to server after maximum attempts');
            this.showConnectionError();
            this.socket.close();
        });

        this.socket.on('connect_error', (error) => {
            console.error('Connection error:', error);
            this.showConnectionError();
        });
    }

    initialize() {
        this.setupResponseHandlers();
        this.setupSocketListeners();
    }

    setupSocketListeners() {
        // Move all socket listeners here from init.js
        this.socket.on('hotkey_push_to_talk_start', () => {
            if (window.startPushToTalk) {
                window.startPushToTalk();
            }
        });

        this.socket.on('hotkey_push_to_talk_stop', () => {
            if (window.stopPushToTalk) {
                window.stopPushToTalk();
            }
        });

        this.socket.on('status_update', (data) => {
            if (!data.isPushToTalk && window.updateListeningUI) {
                window.updateListeningUI(data.listening);
            }
        });

        this.socket.on('audio_finished', () => {
            if (window.speechHandler) {
                window.speechHandler.switchToTriggerMode();
            }
        });
    }

    showConnectionError() {
        const statusElement = document.getElementById('listening-status');
        if (statusElement) {
            statusElement.textContent = 'Server disconnected - Please refresh page';
            statusElement.className = 'status-inactive';
        }
    }

    setupResponseHandlers() {
        this.socket.on('response', async (data) => {
            console.log('Received response:', data);
            
            // Check if this is a long-running task
            if (data.status === 'processing') {
                this.handleLongRunningTask(data.conversation_id);
                return;
            }
            
            // Update text response immediately
            const responseElement = document.getElementById('response');
            if (responseElement) {
                responseElement.textContent = data.text || data.response || 'No response';
            }
            
            // Handle audio if present and voice is enabled
            if (data.audio && this.voiceEnabled) {
                // Request audio focus when playing in background
                if (!window.isPageVisible) {
                    try {
                        await navigator.mediaSession.setActionHandler('play', () => {});
                    } catch (err) {
                        console.warn('MediaSession API not supported', err);
                    }
                }
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

        // Add timer update handler
        this.socket.on('timer_update', (data) => {
            console.log('Timer update:', data);
            this.updateTimerDisplay(data.remaining);
        });

        // Add timer complete handler
        this.socket.on('timer_complete', () => {
            console.log('Timer complete');
            this.handleTimerComplete();
        });
    }

    updateResponseDisplay() {
        const responseElement = document.getElementById('response');
        if (!responseElement) return;

        let html = '';
        
        if (this.currentResponse) {
            html += `<div class="current-response">
                <strong>Current:</strong> ${this.currentResponse}
            </div>`;
        }
        
        if (this.responseQueue.length > 0) {
            html += '<div class="queued-responses">';
            html += '<strong>Queued:</strong>';
            html += '<ul>';
            this.responseQueue.forEach((response, index) => {
                html += `
                    <li>
                        <div class="queued-item">
                            <span>${response}</span>
                            <button class="btn-cancel-queue" onclick="window.socketHandler.removeFromQueue(${index})">
                                <i class="bi bi-x-circle"></i>
                            </button>
                        </div>
                    </li>`;
            });
            html += '</ul></div>';
        }
        
        responseElement.innerHTML = html || 'None';
    }

    async playAudioResponse(audioData, textResponse) {
        // If audio is currently playing, add to queue and return
        if (this.isPlaying) {
            this.audioQueue.push(audioData);
            this.responseQueue.push(textResponse);
            this.updateResponseDisplay();
            console.log('Audio and text added to queue. Queue length:', this.audioQueue.length);
            return;
        }

        try {
            this.currentResponse = textResponse;
            this.updateResponseDisplay();

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
                // Process next audio in queue if any
                this.processAudioQueue();
            };
        } catch (error) {
            console.error('Error playing audio:', error);
            this.isPlaying = false;
            this.currentAudio = null;
            // Try to process next audio in queue even if current one failed
            this.processAudioQueue();
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
                
                // If queue is empty, keep the display but update it
                if (this.audioQueue.length === 0) {
                    this.updateResponseDisplay();
                }
                
                this.socket.emit('audio_finished');
                this.processAudioQueue();
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

    updateTimerDisplay(remainingSeconds) {
        const timerDisplay = document.getElementById('timer-display');
        if (!timerDisplay) {
            console.error('Timer display element not found!');
            return;
        }
        
        console.log('Updating timer display:', {
            remainingSeconds,
            currentDisplay: timerDisplay.style.display,
            element: timerDisplay
        });

        const minutes = Math.floor(remainingSeconds / 60);
        const seconds = remainingSeconds % 60;
        
        document.getElementById('timer-minutes').textContent = String(minutes).padStart(2, '0');
        document.getElementById('timer-seconds').textContent = String(seconds).padStart(2, '0');
        
        // Force display block and remove any hiding class
        timerDisplay.style.display = 'block';
        timerDisplay.classList.remove('hiding');
    }

    handleTimerComplete() {
        const timerDisplay = document.getElementById('timer-display');
        if (!timerDisplay) {
            console.error('Timer display element not found!');
            return;
        }
        
        console.log('Timer complete, playing sound and hiding display');
        
        // Create and play a pleasant "ding" sound
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.type = 'sine';
        oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
        gainNode.gain.setValueAtTime(0.5, audioContext.currentTime);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.8);
        
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.8);
        
        // Animate and hide the timer display
        timerDisplay.classList.add('hiding');
        setTimeout(() => {
            timerDisplay.style.display = 'none';
            timerDisplay.classList.remove('hiding');
        }, 300);
    }

    // Add method to process the audio queue
    async processAudioQueue() {
        if (this.isPlaying || this.audioQueue.length === 0) {
            return;
        }
        
        const nextAudio = this.audioQueue.shift();
        const nextResponse = this.responseQueue.shift();
        await this.playAudioResponse(nextAudio, nextResponse);
    }

    // Add new method for handling long-running tasks
    async handleLongRunningTask(conversationId) {
        console.log('Handling long-running task:', conversationId);
        
        this.updateProcessingStatus(true);

        let retryCount = 0;
        const maxRetries = 30;
        
        try {
            while (retryCount < maxRetries) {
                const response = await fetch(`http://127.0.0.1:8015/pending_response/${conversationId}`);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const data = await response.json();
                
                if (data.status !== 'waiting') {
                    this.updateProcessingStatus(false);
                    console.log('Long-running task completed:', data);
                    
                    // Handle audio if present
                    if (data.audio && this.voiceEnabled) {
                        // Use the queue system with both audio and text
                        if (this.isPlaying) {
                            this.audioQueue.push(data.audio);
                            this.responseQueue.push(data.text || data.response || 'No response');
                            this.updateResponseDisplay();
                            console.log('Audio and text added to queue from long-running task');
                        } else {
                            await this.playAudioResponse(data.audio, data.text || data.response || 'No response');
                        }
                    } else {
                        // If no audio, just update the response immediately
                        this.currentResponse = data.text || data.response || 'No response';
                        this.updateResponseDisplay();
                    }
                    
                    // If we have animation data, handle it
                    if (data.animation_data) {
                        try {
                            const animation_response = await fetch('http://localhost:5001/play_animation', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                },
                                body: JSON.stringify(data.animation_data)
                            });
                            if (!animation_response.ok) {
                                console.error('Animation request failed');
                            }
                        } catch (e) {
                            console.error('Failed to trigger animation:', e);
                        }
                    }
                    
                    return data;
                }
                
                // Wait before next poll
                await new Promise(resolve => setTimeout(resolve, 1000));
                retryCount++;
                
            }
        } catch (error) {
            this.updateProcessingStatus(false);
            console.error('Error polling for response:', error);
        }
        
        if (retryCount >= maxRetries) {
            this.updateProcessingStatus(false);
            console.error('Long-running task timed out');
        }
    }

    // Add method to remove item from queue
    removeFromQueue(index) {
        if (index >= 0 && index < this.responseQueue.length) {
            // Remove both audio and text from queues
            this.audioQueue.splice(index, 1);
            this.responseQueue.splice(index, 1);
            this.updateResponseDisplay();
            console.log(`Removed item ${index} from queue`);
        }
    }

    updateProcessingStatus(isProcessing) {
        const statusElement = document.getElementById('listening-status');
        if (statusElement) {
            if (isProcessing) {
                this.processingCount++;
                statusElement.textContent = 'Processing request...';
                statusElement.className = 'status-processing';
            } else {
                this.processingCount--;
                if (this.processingCount <= 0) {
                    this.processingCount = 0;
                    statusElement.textContent = 'Listening';
                    statusElement.className = 'status-active';
                }
            }
        }
    }
}

// Make socketHandler globally accessible for the onclick handler
window.socketHandler = null;
document.addEventListener('DOMContentLoaded', () => {
    if (window.socket) {
        window.socketHandler = new SocketHandler(window.socket);
    }
}); 