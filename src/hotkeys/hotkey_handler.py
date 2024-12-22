import keyboard
from src.services.status_overlay import AssistantState
from src.utils.logging_config import handle_error
import logging
import requests

logger = logging.getLogger(__name__)

class HotkeyHandler:
    def __init__(self, socketio):
        try:
            logger.debug("Initializing HotkeyHandler")
            self.socketio = socketio
            self.push_to_talk_key = '`'
            self.overlay_url = "http://localhost:8020"  # Overlay service URL
            
            self.setup_hotkeys()
            self.set_state(AssistantState.IDLE)
        except Exception as e:
            handle_error(logger, e, "HotkeyHandler initialization")

    def set_state(self, state):
        """Emit state change event via socketio"""
        try:
            # Emit the state change event
            self.socketio.emit('state_change', {'state': state.value})
            logger.debug(f"Emitted state change: {state.value}")
        except Exception as e:
            handle_error(logger, e, "Emitting state change", silent=True)

    def setup_hotkeys(self):
        logger.debug("Setting up hotkeys")
        keyboard.on_press_key(self.push_to_talk_key, self.handle_push_to_talk_press)
        keyboard.on_release_key(self.push_to_talk_key, self.handle_push_to_talk_release)

    def handle_push_to_talk_press(self, e):
        try:
            logger.debug("Push-to-talk pressed")
            self.set_state(AssistantState.LISTENING)
            self.socketio.emit('hotkey_push_to_talk_start')
        except Exception as e:
            handle_error(logger, e, "Push-to-talk press handling", silent=True)

    def handle_push_to_talk_release(self, e):
        logger.debug("Push-to-talk released")
        self.set_state(AssistantState.IDLE)
        self.socketio.emit('hotkey_push_to_talk_stop')

    def set_speaking_state(self):
        logger.debug("Setting SPEAKING state")
        self.set_state(AssistantState.SPEAKING)

    def set_idle_state(self):
        logger.debug("Setting IDLE state")
        self.set_state(AssistantState.IDLE) 