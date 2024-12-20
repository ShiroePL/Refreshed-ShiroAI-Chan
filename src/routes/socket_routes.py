from flask_socketio import emit
from src.app_instance import socketio, assistant, hotkey_handler, get_vtube_api
from src.overlay.status_overlay import AssistantState
from src.utils.logging_config import handle_error
import logging
from windows_functions.govee_mode_changer import change_lights_mode  # Import the function
from api_functions.anilist_functions import show_media_list
import asyncio
from src.services.timer_service import TimerService


logger = logging.getLogger(__name__)

# Initialize timer service
timer_service = TimerService()

@socketio.on('transcript')
def handle_transcript(data):
    """Handle incoming transcription data."""
    transcript = data.get('transcript', '')
    assistant.last_command = transcript
    
    # Set processing state while getting response
    if hotkey_handler:
        hotkey_handler.overlay.set_state(AssistantState.PROCESSING)
    
    response = assistant.get_response(transcript)
    
    # Get vtube_api safely
    vtube_api = get_vtube_api()
    if vtube_api and vtube_api.connected:
        # Use vtube_api here if needed
        pass
    
    # Debug log for audio data
    if response.get('audio'):
        logger.debug(f"Audio data present, length: {len(response['audio'])}")
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
            
        # Send a special goodbye message before stopping
        response = {
            'text': "さようなら! (Sayounara!) I'll be here when you need me again!",
            'audio': assistant.text_to_speech("さようなら! I'll be here when you need me again!")
        }
        
        # Send the goodbye message and wait for audio to finish
        emit('response', {
            'text': response['text'],
            'transcript': 'sayounara'
        })
        
        if response.get('audio'):
            emit('audio', response['audio'])
        
        # Update UI status
        emit('status_update', {'listening': False})
        
        # Signal complete shutdown after response is sent
        emit('shutdown_complete')
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

@socketio.on('state_change')
def handle_state_change(data):
    """Handle state change events from frontend."""
    try:
        new_state = data.get('state')
        if new_state and hotkey_handler:
            if new_state == 'LISTENING_FOR_COMMAND':
                hotkey_handler.overlay.set_state(AssistantState.LISTENING_COMMAND)
            elif new_state == 'LISTENING_FOR_TRIGGER':
                hotkey_handler.overlay.set_state(AssistantState.LISTENING)
            # ... other states remain the same
    except Exception as e:
        handle_error(logger, e, "State change handler", silent=True)

@socketio.on('action')
def handle_action(data):
    """Handle action commands from frontend"""
    try:
        action_type = data.get('type')
        
        if action_type == 'govee_lights':
            mode = data.get('mode', 'dxgi')
            result = change_lights_mode(mode)
            
            # Just emit a simple confirmation without triggering assistant response
            emit('action_response', {
                'type': action_type,
                'success': True,
                'message': f'Lights mode changed to {mode}'
            })
            
        if action_type == 'tea_timer':
            duration = data.get('duration', 15)  # Default to 15 seconds for testing
            logger.info(f"Starting tea timer for {duration} seconds")
            success = timer_service.start_timer(duration)

            if success:
                message = f"Tea timer started for {duration} seconds"
                logger.info(message)
                
                # Get vtube_api safely and play animation if available
                vtube_api = get_vtube_api()
                if vtube_api and vtube_api.connected:
                    try:
                        vtube_api.play_animation("introduce")
                        logger.debug("VTube animation played successfully")
                    except Exception as e:
                        logger.error(f"Failed to play VTube animation: {e}")
            else:
                message = "Timer already running!"
                logger.warning(message)

            emit('action_response', {
                'type': action_type,
                'success': success,
                'message': message
            })
            
            # Also emit a regular response for the UI
            emit('response', {
                'text': message,
                'transcript': 'Starting tea timer'
            })
            
        if action_type == 'show_media_list':
            content_type = data.get('content_type')
            # Run the async function in a synchronous context
            response_text = asyncio.run(show_media_list(content_type))
            
            emit('response', {
                'text': response_text,
                'transcript': f"Showing your {content_type.lower()} list"
            })
        
    except Exception as e:
        handle_error(logger, e, f"Action handler: {data.get('type')}")
        emit('action_response', {
            'type': data.get('type'),
            'success': False,
            'message': str(e)
        })
    