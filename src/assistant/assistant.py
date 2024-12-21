import logging
from src.config.azure_config import get_groq_api_keys
from .response_handler import ResponseHandler
from src.services.ai_service import GroqService
from src.utils.error_handler import handle_error

logger = logging.getLogger(__name__)

class SimpleAssistant:
    def __init__(self):
        try:
            self.listening = False
            self.last_command = ""
            self.response = ""
            self.running = True
            
            # Initialize Groq service
            api_keys = get_groq_api_keys()
            self.groq_service = GroqService(api_keys)
            
            # Initialize response handler with Groq service
            self.response_handler = ResponseHandler()
            self.response_handler.set_groq_service(self.groq_service)
            
            logger.info("Assistant initialized successfully")
        except Exception as e:
            handle_error(logger, e, "Assistant initialization")

    def get_response(self, command):
        """Get response from the response handler."""
        try:
            response_text = self.response_handler.handle_response(command, self)
            return {
                'text': response_text
            }
        except Exception as e:
            handle_error(logger, e, "Getting assistant response")
            return {
                'text': "I encountered an error processing your request."
            } 