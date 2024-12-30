import sys
import os
# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify
from modules.vtube.vtube_studio_api import VTubeStudioAPI
import threading
import logging
from flask_socketio import SocketIO
import json
from modules.vtube.animation_analyzer import AnimationAnalyzer
from typing import Dict
from src.utils.logging_config import setup_logger
from src.config.service_config import AI_SERVICE_URL
import httpx
import time

# Setup logging
logger = setup_logger("animation")


app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

class AnimationController:
    def __init__(self):
        self.vtube_api = None
        self.analyzer = AnimationAnalyzer()
        self.ai_service_url = AI_SERVICE_URL  # Store AI service URL
        self.connect_to_vtube()

    def connect_to_vtube(self):
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                self.vtube_api = VTubeStudioAPI()
                logger.info("VTube Studio API connected successfully")
                return
            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    logger.warning(f"VTube Studio connection attempt {retry_count}/{max_retries} failed: {e}")
                    time.sleep(2)  # Wait 2 seconds before retrying
                else:
                    logger.error(f"Failed to connect to VTube Studio after {max_retries} attempts: {e}")
                    self.vtube_api = None
                    raise

    async def analyze_and_play_animation(self, text: str, ai_response: Dict = None, context: Dict = None):
        """Analyze text and context to determine appropriate animation"""
        try:
            if not self.vtube_api or not self.vtube_api.connected:
                logger.error("VTube Studio API not connected")
                return False, "VTube Studio not connected"

            # Use analyzer to determine best animation
            animation, confidence = self.analyzer.analyze(
                text=text,
                ai_response=ai_response or {},
                context=context or {}
            )

            logger.info(f"Selected animation '{animation}' with confidence {confidence}")
            self.vtube_api.play_animation(animation)
            return True, f"Played animation: {animation}"

        except Exception as e:
            logger.error(f"Error playing animation: {e}")
            return False, str(e)

# Create global animation controller
animation_controller = None

def create_controller():
    global animation_controller
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            animation_controller = AnimationController()
            logger.info("Animation controller initialized successfully")
            return
        except Exception as e:
            retry_count += 1
            if retry_count < max_retries:
                logger.warning(f"Failed to initialize animation controller (attempt {retry_count}/{max_retries}): {e}")
                time.sleep(2)  # Wait 2 seconds before retrying
            else:
                logger.error(f"Failed to initialize animation controller after {max_retries} attempts: {e}")
                animation_controller = None
                return

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
        ai_response = data.get('ai_response', {})
        context = data.get('context', {})
        
        # Create a sanitized version of ai_response for logging
        log_safe_response = {
            'text': ai_response.get('text', ''),
            'success': ai_response.get('success', False),
            # Indicate audio presence without logging the data
            'audio': '<audio_data_present>' if 'audio' in ai_response else None
        }
        
        logger.info(f"Received animation request - text: {text}, ai_response: {log_safe_response}, context: {context}")
        success, message = animation_controller.analyze_and_play_animation(text, ai_response, context)
        
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
        
        if not animation_controller:
            logger.warning("Starting VTube Animation Server without VTube Studio connection...")
        else:
            logger.info("Starting VTube Animation Server with VTube Studio connected...")
            
        socketio.run(app, host='127.0.0.1', port=5001, debug=True)
    except Exception as e:
        logger.error(f"Server startup failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 