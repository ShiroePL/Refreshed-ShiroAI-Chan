from flask_socketio import emit
import requests
from src.app_instance import socketio, assistant, hotkey_handler
from src.services.status_overlay import AssistantState
from src.utils.logging_config import setup_logger, handle_error
import asyncio
from windows_functions.govee_mode_changer import change_lights_mode
from api_functions.anilist_functions import show_media_list
from src.services.timer_service import TimerService
import uuid

# Setup module-specific logger
logger = setup_logger('socket_routes')

# Initialize timer service with socketio instance
timer_service = TimerService(socketio)

# Replace WebSocket URL with HTTP URL
BRAIN_SERVICE_URL = 'http://127.0.0.1:8015/process'

def send_to_brain_service(data):
    """Send data to Brain service via HTTP"""
    try:
        # Make HTTP POST request to Brain service
        response = requests.post(BRAIN_SERVICE_URL, json={
            'transcript': data.get('transcript', ''),
            'skip_vtube': data.get('skip_vtube', False),
            'use_openai': data.get('use_openai', False),
            'context': data.get('context', {}),
            'conversation_id': str(uuid.uuid4())  # Generate unique ID for each request
        })
        response.raise_for_status()
        response_data = response.json()
        
        # If it's a long-running task, emit the processing status
        if response_data.get('status') == 'processing':
            emit('response', {
                'status': 'processing',
                'conversation_id': response_data.get('conversation_id')
            })
            return None
            
        # Strip out animation data before sending initial response
        animation_data = response_data.pop('animation_data', None)
        
        # Emit response to client (this will trigger audio playback)
        emit('response', response_data)
        
        # If we have animation data, trigger it immediately after sending response
        if animation_data:
            try:
                # Send animation request to VTube service
                animation_response = requests.post(
                    'http://localhost:5001/play_animation',
                    json=animation_data
                )
                animation_response.raise_for_status()
                logger.info(f"Animation triggered successfully: {animation_data.get('message', 'unknown animation')}")
            except Exception as e:
                logger.error(f"Failed to trigger animation: {e}")
        
        # Update overlay state based on response
        if hotkey_handler:
            if response_data.get('audio'):
                hotkey_handler.set_state(AssistantState.SPEAKING)
            else:
                hotkey_handler.set_state(AssistantState.LISTENING)
                
        return response_data
        
    except Exception as e:
        logger.error(f"[ERROR] Brain service communication failed: {e}")
        if hotkey_handler:
            hotkey_handler.set_state(AssistantState.ERROR)
        emit('error', {'message': str(e)})
        return None

@socketio.on('transcript')
def handle_transcript(data):
    """Handle incoming transcription data."""
    try:
        transcript = data.get('transcript', '')
        skip_vtube = data.get('skip_vtube', False)
        use_openai = data.get('use_openai', False)
        logger.info(f"[TRANSCRIPT] Received data: {data}")
        logger.info(f"[TRANSCRIPT] use_openai flag: {use_openai}")
        
        if hotkey_handler:
            hotkey_handler.set_state(AssistantState.PROCESSING)
            
        # Send to Brain service with all flags
        request_data = {
            'type': 'process',
            'transcript': transcript,
            'skip_vtube': skip_vtube,
            'use_openai': use_openai
        }
        logger.info(f"[TRANSCRIPT] Sending to brain: {request_data}")  # Log what we're sending
        send_to_brain_service(request_data)
        
    except Exception as e:
        logger.error(f"[ERROR] Transcript handling failed: {e}")
        emit('error', {'message': str(e)})
        if hotkey_handler:
            hotkey_handler.set_state(AssistantState.ERROR)

@socketio.on('start_listening')
def handle_start_listening():
    """Handle start listening event."""
    assistant.listening = True
    if hotkey_handler:
        hotkey_handler.set_state(AssistantState.LISTENING)
    emit('status_update', {'listening': True})

@socketio.on('stop_listening')
def handle_stop_listening():
    """Handle stop listening event."""
    try:
        assistant.listening = False
        if hotkey_handler:
            hotkey_handler.set_state(AssistantState.IDLE)
            
        # Send a special goodbye message to the AI service
        emit('response', {
            'text': "さようなら! (Sayounara!) I'll be here when you need me again!",
            'transcript': 'sayounara'
        })
        
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
            # Check if we're in text mode
            if hasattr(assistant, 'text_mode') and assistant.text_mode:
                hotkey_handler.set_state(AssistantState.IDLE)
            else:
                if hasattr(assistant, 'listening') and assistant.listening:
                    hotkey_handler.set_state(AssistantState.LISTENING)
                else:
                    hotkey_handler.set_state(AssistantState.IDLE)
    except Exception as e:
        handle_error(logger, e, "Audio finished handler")

@socketio.on('push_to_talk_start')
def handle_push_to_talk_start():
    """Handle push-to-talk start event."""
    try:
        if hotkey_handler:
            hotkey_handler.set_state(AssistantState.LISTENING)
    except Exception as e:
        handle_error(logger, e, "Push-to-talk start handler", silent=True)

@socketio.on('push_to_talk_stop')
def handle_push_to_talk_stop():
    """Handle push-to-talk stop event."""
    try:
        if hotkey_handler:
            hotkey_handler.set_state(AssistantState.IDLE)
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
            duration = data.get('duration', 15)
            logger.info(f"Starting tea timer for {duration} seconds")
            success = timer_service.start_timer(duration)

            if success:
                message = f"Tea timer started for {duration} seconds"
                logger.info(message)
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
    
@socketio.on('keepalive')
def handle_keepalive():
    """Handle keepalive ping from client"""
    emit('keepalive_response', {'status': 'ok'})
    
@socketio.on('text_mode_start')
def handle_text_mode_start():
    """Handle switching to text-only mode"""
    try:
        # Set a flag on the assistant to indicate text mode
        assistant.text_mode = True
        assistant.listening = False
        if hotkey_handler:
            hotkey_handler.set_state(AssistantState.IDLE)
    except Exception as e:
        handle_error(logger, e, "Text mode start handler")

@socketio.on('text_mode_end')
def handle_text_mode_end():
    """Handle switching back from text-only mode"""
    try:
        # Remove text mode flag
        assistant.text_mode = False
    except Exception as e:
        handle_error(logger, e, "Text mode end handler")
    