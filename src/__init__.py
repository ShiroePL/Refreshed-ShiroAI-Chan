from src.app_instance import app, socketio, assistant

# Import routes first
from src.routes import main_routes, socket_routes

# Initialize hotkey handler after routes are imported
from src.hotkeys.hotkey_handler import HotkeyHandler
from src.app_instance import hotkey_handler

# Create and store hotkey handler instance
hotkey_handler = HotkeyHandler(socketio)