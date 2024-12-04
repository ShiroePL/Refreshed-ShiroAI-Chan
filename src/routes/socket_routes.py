from flask_socketio import emit
from src.app_instance import socketio, assistant, hotkey_handler
from src.overlay.status_overlay import AssistantState
import logging

logger = logging.getLogger(__name__)

@socketio.on('transcript')
def handle_transcript(data):
    """Handle incoming transcription data."""
    transcript = data.get('transcript', '')
    assistant.last_command = transcript
    
    # Set processing state while getting response
    if hotkey_handler:
        hotkey_handler.overlay.set_state(AssistantState.PROCESSING)
    
    response = assistant.get_response(transcript)
    
    # Set speaking state only if voice is enabled
    if hotkey_handler and response.get('audio'):
        hotkey_handler.overlay.set_state(AssistantState.SPEAKING)
    else:
        # If no audio response, return to previous state
        if assistant.listening:
            hotkey_handler.overlay.set_state(AssistantState.LISTENING)
        else:
            hotkey_handler.overlay.set_state(AssistantState.IDLE)
    
    emit('response', {
        'text': response['text'],
        'audio': response['audio'],
        'transcript': transcript
    })

@socketio.on('start_listening')
def handle_start_listening():
    """Handle start listening event."""
    assistant.listening = True
    if hotkey_handler:
        hotkey_handler.overlay.set_state(AssistantState.LISTENING)
    emit('status_update', {'listening': True})

@socketio.on('stop_listening')
def handle_stop_listening():
    """Handle stop listening event."""
    assistant.listening = False
    if hotkey_handler:
        hotkey_handler.overlay.set_state(AssistantState.IDLE)
    emit('status_update', {'listening': False})

@socketio.on('audio_finished')
def handle_audio_finished():
    """Handle audio playback finished event."""
    if hotkey_handler:
        # Return to listening state if toggle is on, otherwise idle
        if assistant.listening:
            hotkey_handler.overlay.set_state(AssistantState.LISTENING)
        else:
            hotkey_handler.overlay.set_state(AssistantState.IDLE)

@socketio.on('push_to_talk_start')
def handle_push_to_talk_start():
    """Handle push-to-talk start event."""
    if hotkey_handler:
        hotkey_handler.overlay.set_state(AssistantState.LISTENING)
    # Note: We don't update assistant.listening here

@socketio.on('push_to_talk_stop')
def handle_push_to_talk_stop():
    """Handle push-to-talk stop event."""
    if hotkey_handler:
        hotkey_handler.overlay.set_state(AssistantState.IDLE)
    # Note: We don't update assistant.listening here 