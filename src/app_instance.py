from flask import Flask
from flask_socketio import SocketIO
from src.assistant.assistant import SimpleAssistant


# Create Flask app
app = Flask(__name__, 
           template_folder='../templates',
           static_folder='../static')

# Create SocketIO instance with configuration
socketio = SocketIO(
    app,
    ping_timeout=60,
    ping_interval=25,
    cors_allowed_origins="*"
)

# Create assistant instance
assistant = SimpleAssistant()

# Create overlay instance

# Create a variable to store hotkey_handler (will be set later)
hotkey_handler = None 

