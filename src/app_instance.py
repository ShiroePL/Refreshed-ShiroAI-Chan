from flask import Flask
from flask_socketio import SocketIO

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

# Create a variable to store hotkey_handler (will be set later)
hotkey_handler = None

# Create a variable for assistant (will be initialized in init_app)
assistant = None

def init_app():
    """Initialize the application and its dependencies."""
    global assistant
    
    # Only initialize assistant if it hasn't been initialized yet
    if assistant is None:
        from src.services.assistant_service import AssistantService
        assistant = AssistantService()

    # Import routes after app is created
    from src.routes import socket_routes, web_routes

