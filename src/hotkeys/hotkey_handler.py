import keyboard

class HotkeyHandler:
    def __init__(self, socketio):
        self.socketio = socketio
        self.push_to_talk_key = '`'  # Default key
        self.setup_hotkeys()

    def setup_hotkeys(self):
        keyboard.on_press_key(self.push_to_talk_key, self.handle_push_to_talk_press)
        keyboard.on_release_key(self.push_to_talk_key, self.handle_push_to_talk_release)

    def handle_push_to_talk_press(self, e):
        self.socketio.emit('hotkey_push_to_talk_start')

    def handle_push_to_talk_release(self, e):
        self.socketio.emit('hotkey_push_to_talk_stop') 