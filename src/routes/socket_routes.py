from flask_socketio import emit
from src import socketio, assistant

@socketio.on('transcript')
def handle_transcript(data):
    """Handle incoming transcription data."""
    transcript = data.get('transcript', '')
    assistant.last_command = transcript
    response = assistant.get_response(transcript)
    emit('response', {
        'text': response['text'],
        'audio': response['audio'],
        'transcript': transcript
    })

@socketio.on('start_listening')
def handle_start_listening():
    """Handle start listening event."""
    assistant.listening = True
    emit('status_update', {'listening': True})

@socketio.on('stop_listening')
def handle_stop_listening():
    """Handle stop listening event."""
    assistant.listening = False
    emit('status_update', {'listening': False}) 