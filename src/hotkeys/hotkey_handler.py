import keyboard
from src.overlay.status_overlay import StatusOverlay, AssistantState
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class HotkeyHandler:
    def __init__(self, socketio):
        logger.debug("Initializing HotkeyHandler")
        self.socketio = socketio
        self.push_to_talk_key = '`'  # Default key
        self.overlay = StatusOverlay.get_instance()
        self.setup_hotkeys()
        # Start in idle state
        self.overlay.set_state(AssistantState.IDLE)
        logger.debug("HotkeyHandler initialized")

    def setup_hotkeys(self):
        logger.debug("Setting up hotkeys")
        keyboard.on_press_key(self.push_to_talk_key, self.handle_push_to_talk_press)
        keyboard.on_release_key(self.push_to_talk_key, self.handle_push_to_talk_release)

    def handle_push_to_talk_press(self, e):
        logger.debug("Push-to-talk pressed")
        if self.overlay.current_state != AssistantState.LISTENING:
            self.overlay.set_state(AssistantState.LISTENING)
        self.socketio.emit('hotkey_push_to_talk_start')

    def handle_push_to_talk_release(self, e):
        logger.debug("Push-to-talk released")
        if self.overlay.current_state == AssistantState.LISTENING:
            self.overlay.set_state(AssistantState.IDLE)
        self.socketio.emit('hotkey_push_to_talk_stop')

    def set_speaking_state(self):
        logger.debug("Setting SPEAKING state")
        self.overlay.set_state(AssistantState.SPEAKING)

    def set_idle_state(self):
        logger.debug("Setting IDLE state")
        self.overlay.set_state(AssistantState.IDLE) 