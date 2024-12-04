import keyboard
from src.overlay.status_overlay import StatusOverlay, AssistantState

class HotkeyHandler:
    def __init__(self, socketio):
        self.socketio = socketio
        self.push_to_talk_key = '`'  # Default key
        self.overlay = StatusOverlay.get_instance()
        self.setup_hotkeys()

    def setup_hotkeys(self):
        keyboard.on_press_key(self.push_to_talk_key, self.handle_push_to_talk_press)
        keyboard.on_release_key(self.push_to_talk_key, self.handle_push_to_talk_release)

    def handle_push_to_talk_press(self, e):
        self.overlay.set_state(AssistantState.LISTENING)
        self.socketio.emit('hotkey_push_to_talk_start')

    def handle_push_to_talk_release(self, e):
        self.overlay.set_state(AssistantState.PROCESSING)
        self.socketio.emit('hotkey_push_to_talk_stop')

    def set_speaking_state(self):
        self.overlay.set_state(AssistantState.SPEAKING)

    def set_idle_state(self):
        self.overlay.set_state(AssistantState.IDLE) 