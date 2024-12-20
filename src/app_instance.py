from flask import Flask
from flask_socketio import SocketIO
from src.assistant.assistant import SimpleAssistant
from src.overlay.status_overlay import StatusOverlay

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

# Create overlay instance
overlay = StatusOverlay.get_instance()

# Create a variable to store hotkey_handler (will be set later)
hotkey_handler = None 

def trigger_animation(text, mood=None):
    """Send animation request to VTube animation server"""
    try:
        response = requests.post(
            'http://127.0.0.1:5001/play_animation',
            json={'text': text, 'mood': mood},
            timeout=1  # Short timeout to prevent blocking
        )
        if response.status_code == 200:
            logger.debug("Animation request successful")
        else:
            logger.warning(f"Animation request failed: {response.json().get('message')}")
    except Exception as e:
        logger.error(f"Error sending animation request: {e}")