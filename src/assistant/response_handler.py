import time
from src.services.groq_service import GroqService
from src.config.azure_config import get_groq_api_keys

class ResponseHandler:
    def __init__(self):
        api_keys = get_groq_api_keys()
        self.groq_service = GroqService(api_keys)

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
            response = self.groq_service.send_to_groq(command)
            return response
        except Exception as e:
            print(f"Error getting AI response: {e}")
            return "I'm having trouble processing that right now. Could you try again?"

def handle_stop(assistant):
    """Handle the stop command."""
    assistant.listening = False
    return "Stopping listening!" 