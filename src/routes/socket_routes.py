from flask_socketio import emit
from src.app_instance import socketio, assistant, hotkey_handler
from src.overlay.status_overlay import AssistantState
from src.utils.logging_config import handle_error
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
    
    # Debug log for audio data
    if response.get('audio'):
        logger.debug(f"Audio data present, length: {len(response['audio'])}")
        # Emit audio data separately
        emit('audio', response['audio'])
    else:
        logger.debug("No audio data in response")
    
    # Set speaking state only if voice is enabled
    if hotkey_handler and response.get('audio'):
        hotkey_handler.overlay.set_state(AssistantState.SPEAKING)
    else:
        if assistant.listening:
            hotkey_handler.overlay.set_state(AssistantState.LISTENING)
        else:
            hotkey_handler.overlay.set_state(AssistantState.IDLE)
    
    # Send text response
    emit('response', {
        'text': response['text'],
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
    try:
        assistant.listening = False
        if hotkey_handler:
            hotkey_handler.overlay.set_state(AssistantState.IDLE)
        emit('status_update', {'listening': False})
    except Exception as e:
        handle_error(logger, e, "Stop listen handler")

@socketio.on('audio_finished')
def handle_audio_finished():
    """Handle audio playback finished event."""
    try:
        if hotkey_handler:
            if assistant.listening:
                hotkey_handler.overlay.set_state(AssistantState.LISTENING)
            else:
                hotkey_handler.overlay.set_state(AssistantState.IDLE)
    except Exception as e:
        handle_error(logger, e, "Audio finished handler")

@socketio.on('push_to_talk_start')
def handle_push_to_talk_start():
    """Handle push-to-talk start event."""
    try:
        if hotkey_handler:
            hotkey_handler.overlay.set_state(AssistantState.LISTENING)
    except Exception as e:
        handle_error(logger, e, "Push-to-talk start handler", silent=True)

@socketio.on('push_to_talk_stop')
def handle_push_to_talk_stop():
    """Handle push-to-talk stop event."""
    try:
        if hotkey_handler:
            hotkey_handler.overlay.set_state(AssistantState.IDLE)
    except Exception as e:
        handle_error(logger, e, "Push-to-talk stop handler", silent=True)
    