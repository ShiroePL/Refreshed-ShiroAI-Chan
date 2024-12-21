import sys
import os
# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify
from services.vtube.vtube_studio_api import VTubeStudioAPI
import threading
import logging
from flask_socketio import SocketIO
import json

# Setup logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

class AnimationController:
    def __init__(self):
        self.vtube_api = None
        self.connect_to_vtube()

    def connect_to_vtube(self):
        try:
            self.vtube_api = VTubeStudioAPI()
            logger.info("VTube Studio API connected successfully")
        except Exception as e:
            logger.error(f"Failed to connect to VTube Studio: {e}")
            raise  # Re-raise to see the full error

    def analyze_and_play_animation(self, text, mood=None):
        """Analyze text and mood to determine appropriate animation"""
        try:
            if not self.vtube_api or not self.vtube_api.connected:
                logger.error("VTube Studio API not connected")
                return False, "VTube Studio not connected"

            # Map mood directly to animation if provided
            if mood:
                animation = mood
            # Otherwise analyze text
            elif "happy" in text.lower():
                animation = "happy"
            elif "sad" in text.lower():
                animation = "sad"
            else:
                animation = "introduce"  # default animation

            logger.info(f"Playing animation: {animation}")
            self.vtube_api.play_animation(animation)
            return True, f"Played animation: {animation}"

        except Exception as e:
            logger.error(f"Error playing animation: {e}")
            return False, str(e)

# Create global animation controller
animation_controller = None

def create_controller():
    global animation_controller
    try:
        animation_controller = AnimationController()
        logger.info("Animation controller initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize animation controller: {e}")
        raise

@app.route('/play_animation', methods=['POST'])
def play_animation():
    try:
        if not animation_controller:
            return jsonify({
                'success': False,
                'message': "Animation controller not initialized"
            }), 500

        data = request.json
        text = data.get('text', '')
        mood = data.get('mood')
        
        logger.info(f"Received animation request - text: {text}, mood: {mood}")
        success, message = animation_controller.analyze_and_play_animation(text, mood)
        
        return jsonify({
            'success': success,
            'message': message
        })
    except Exception as e:
        logger.error(f"Error handling animation request: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

def main():
    try:
        # Initialize controller before starting server
        create_controller()
        logger.info("Starting VTube Animation Server on port 5001...")
        socketio.run(app, host='127.0.0.1', port=5001, debug=True)
    except Exception as e:
        logger.error(f"Server startup failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 