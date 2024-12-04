from flask import Flask
from flask_socketio import SocketIO
from src.assistant.assistant import SimpleAssistant

app = Flask(__name__, 
           template_folder='../templates',
           static_folder='../static')
socketio = SocketIO(app)
assistant = SimpleAssistant()

# Import routes after app initialization
from src.routes import main_routes, socket_routes

# Initialize hotkey handler after socketio is fully set up
from src.hotkeys.hotkey_handler import HotkeyHandler
hotkey_handler = HotkeyHandler(socketio)