
from flask import Flask
from flask_socketio import SocketIO

from src.assistant.assistant import SimpleAssistant


# Create Flask app
app = Flask(__name__, 
           template_folder='../templates',
           static_folder='../static')

# Create SocketIO instance
socketio = SocketIO(
    app,
    ping_timeout=10,
    ping_interval=5,
    cors_allowed_origins="*",
    reconnection=True,
    reconnection_attempts=5,
    reconnection_delay=1000,
    reconnection_delay_max=5000
)

# Create assistant instance
assistant = SimpleAssistant()



# Create a variable to store hotkey_handler (will be set later)
hotkey_handler = None 

