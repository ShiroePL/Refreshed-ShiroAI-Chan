from flask_socketio import emit
from src.app_instance import socketio, assistant, hotkey_handler
from src.services.status_overlay import AssistantState
from src.utils.logging_config import handle_error
import logging
import websockets
import json
import asyncio
from functools import partial
from windows_functions.govee_mode_changer import change_lights_mode
from api_functions.anilist_functions import show_media_list
from src.services.timer_service import TimerService
from contextlib import asynccontextmanager
from typing import Optional

logger = logging.getLogger(__name__)

# Initialize timer service
timer_service = TimerService()

# WebSocket connection to Brain service
BRAIN_SERVICE_URL = 'ws://localhost:8015/ws'

class BrainWebSocket:
    def __init__(self):
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.connected = False
        self._connect_lock = asyncio.Lock()
        self._loop = None
        
    def _get_loop(self):
        """Get or create event loop"""
        if self._loop is None or self._loop.is_closed():
            self._loop = asyncio.new_event_loop()
        return self._loop
        
    async def ensure_connected(self):
        """Ensure WebSocket connection is established"""
        if not self.connected:
            async with self._connect_lock:
                if not self.connected:
                    try:
                        logger.info("🔌 Establishing connection to Brain service...")
                        self.websocket = await websockets.connect(BRAIN_SERVICE_URL)
                        self.connected = True
                        logger.info("✅ Connected to Brain service")
                    except Exception as e:
                        logger.error(f"❌ Failed to connect to Brain service: {e}")
                        raise

    async def send_message(self, data: dict) -> dict:
        """Send message to Brain service and get response"""
        await self.ensure_connected()
        try:
            await self.websocket.send(json.dumps(data))
            response = await self.websocket.recv()
            return json.loads(response)
        except Exception as e:
            logger.error(f"❌ Error in Brain communication: {e}")
            self.connected = False
            self.websocket = None
            raise

    def run_async(self, coro):
        """Run coroutine in the event loop"""
        loop = self._get_loop()
        return loop.run_until_complete(coro)

# Create global WebSocket instance
brain_ws = BrainWebSocket()

def send_to_brain_service(data):
    """Send data to Brain service via WebSocket"""
    try:
        # Run async code in sync context
        response_data = brain_ws.run_async(brain_ws.send_message(data))
        
        # Emit response to client
        emit('response', response_data)
        
        # Update overlay state based on response
        if hotkey_handler:
            if response_data.get('audio'):
                hotkey_handler.set_state(AssistantState.SPEAKING)
            else:
                hotkey_handler.set_state(AssistantState.LISTENING)
                
        return response_data
            
    except Exception as e:
        logger.error(f"❌ Error communicating with Brain service: {e}")
        if hotkey_handler:
            hotkey_handler.set_state(AssistantState.ERROR)
        emit('error', {'message': str(e)})
        return None

@socketio.on('transcript')
def handle_transcript(data):
    """Handle incoming transcription data."""
    try:
        transcript = data.get('transcript', '')
        logger.info(f"Received transcript: {transcript}")
        
        if hotkey_handler:
            hotkey_handler.set_state(AssistantState.PROCESSING)
        
        # Send to Brain service
        send_to_brain_service({
            'type': 'process',
            'transcript': transcript
        })
        
    except Exception as e:
        logger.error(f"Error handling transcript: {e}")
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
            if assistant.listening:
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
                
                # Send animation request to VTube server
                trigger_animation(message, mood="introduction")
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
    
# Initialize WebSocket connection when the module loads
@socketio.on('connect')
def handle_connect():
    """Handle client connection by ensuring Brain service connection"""
    try:
        brain_ws.run_async(brain_ws.ensure_connected())
        logger.info("✅ Client connected and Brain service connection established")
    except Exception as e:
        logger.error(f"❌ Failed to establish Brain service connection: {e}")
    