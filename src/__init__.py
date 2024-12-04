from src.app_instance import app, socketio, assistant, overlay

# Import routes first
from src.routes import main_routes, socket_routes

# Initialize hotkey handler after routes are imported
from src.hotkeys.hotkey_handler import HotkeyHandler

# Create hotkey handler instance and store it in app_instance
from src.app_instance import hotkey_handler
import src.app_instance as app_instance
app_instance.hotkey_handler = HotkeyHandler(socketio)

# Make hotkey_handler available to socket_routes
socket_routes.hotkey_handler = app_instance.hotkey_handler