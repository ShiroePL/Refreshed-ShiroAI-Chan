from flask import Flask
from flask_socketio import SocketIO
from src.assistant.assistant import SimpleAssistant
from src.overlay.status_overlay import StatusOverlay

# Create Flask app
app = Flask(__name__, 
           template_folder='../templates',
           static_folder='../static')

# Create SocketIO instance
socketio = SocketIO(app)

# Create assistant instance
assistant = SimpleAssistant()

# Create overlay instance
overlay = StatusOverlay.get_instance()

# Create a variable to store hotkey_handler (will be set later)
hotkey_handler = None 

# Initialize vtube_api as None
vtube_api = None

def connect_to_vtube():
    def _connect():
        try:
            global vtube_api
            vtube_api = VTubeStudioAPI()
            logger.info("VTube Studio API connected successfully")
        except Exception as e:
            logger.error(f"Failed to connect to VTube Studio: {e}")
    
    # Start connection in separate thread
    vtube_thread = threading.Thread(target=_connect)
    vtube_thread.daemon = True
    vtube_thread.start()

def disconnect_from_vtube():
    try:
        global vtube_api
        if vtube_api and hasattr(vtube_api, 'close'):
            vtube_api.close()
            logger.info("VTube Studio API disconnected successfully")
    except Exception as e:
        logger.error(f"Error disconnecting from VTube Studio: {e}")

def get_vtube_api():
    """Safe way to access vtube_api"""
    global vtube_api
    return vtube_api

# Connect to VTube Studio in background thread
connect_to_vtube()