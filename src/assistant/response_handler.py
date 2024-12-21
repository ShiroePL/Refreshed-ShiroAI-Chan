import time
import logging
from src.utils.error_handler import handle_error

logger = logging.getLogger(__name__)

class ResponseHandler:
    def __init__(self, groq_service=None):
        self.groq_service = groq_service

    def set_groq_service(self, groq_service):
        """Set the GroqService instance after initialization"""
        self.groq_service = groq_service

    def handle_response(self, command, assistant):
        """Handle different types of commands and return appropriate responses."""
        command = command.lower()
        
        # Special commands that bypass AI
        if 'stop' in command:
            return handle_stop(assistant)
            
        if not command.strip():
            return "I didn't hear anything. Could you please repeat that?"

        # Get AI response for everything else
        try:
            if not self.groq_service:
                return "Groq service not initialized"
            response = self.groq_service.send_to_groq(command)
            return response
        except Exception as e:
            logger.error(f"Error getting AI response: {e}")
            return "I'm having trouble processing that right now. Could you try again?"

def handle_stop(assistant):
    """Handle the stop command."""
    assistant.listening = False
    return "Stopping listening!" 