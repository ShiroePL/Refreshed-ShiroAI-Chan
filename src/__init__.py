# First, import the logging configuration
from src.utils.logging_config import setup_logger

# Setup base logger for src package
logger = setup_logger('src')

# Then import the app instance
from src.app_instance import app, socketio, assistant

# Import hotkey handler
from src.hotkeys.hotkey_handler import HotkeyHandler

# Create hotkey handler instance
import src.app_instance as app_instance
app_instance.hotkey_handler = HotkeyHandler(socketio)

# Finally import routes
from src.routes import main_routes, socket_routes

# Make hotkey_handler available to socket_routes
socket_routes.hotkey_handler = app_instance.hotkey_handler