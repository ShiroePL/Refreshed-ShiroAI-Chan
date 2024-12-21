from flask import Flask
from flask_socketio import SocketIO
from src.assistant.assistant import SimpleAssistant


# Create Flask app
app = Flask(__name__, 
           template_folder='../templates',
           static_folder='../static')

# Create SocketIO instance
socketio = SocketIO(app)

# Create assistant instance
assistant = SimpleAssistant()

# Create overlay instance

# Create a variable to store hotkey_handler (will be set later)
hotkey_handler = None 

