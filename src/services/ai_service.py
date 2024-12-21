import time
from groq import Groq
import logging
from src.utils.error_handler import handle_error

logger = logging.getLogger(__name__)

def mask_api_key(key: str) -> str:
    """Mask API key for logging, showing only first 4 and last 4 characters"""
    if len(key) < 8:
        return "****"
    return f"{key[:4]}...{key[-4:]}"

class GroqService:
    def __init__(self, api_keys):
        logger.info(f"Initializing GroqService with api_keys type: {type(api_keys)}")
        if not isinstance(api_keys, list):
            logger.error(f"Expected api_keys to be a list, got {type(api_keys)}")
            raise TypeError(f"api_keys must be a list, got {type(api_keys)}")
            
        if not api_keys:
            logger.error("api_keys list is empty")
            raise ValueError("api_keys list cannot be empty")
            
        self.api_keys = api_keys
        self.current_key_index = 0
        self.token_count = 0
        self.start_time = None
        self.basic_prompt = "You are Shiro, a helpful and cheerful AI assistant."
        
        try:
            api_key = self.api_keys[self.current_key_index]
            logger.info(f"Using API key: {mask_api_key(api_key)}")  # Use masking function
            self.client = Groq(api_key=api_key)
            logger.info("Groq service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Groq client: {str(e)}")
            handle_error(logger, e, "Groq service initialization")
            raise

    def reset_token_count(self):
        self.token_count = 0
        self.start_time = None

    def rotate_api_key(self):
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        self.client = Groq(api_key=self.api_keys[self.current_key_index])
        logger.debug(f"Rotated API key to: {self.current_key_index}")

    def send_to_groq(self, user_message):
        """Send a message to Groq API and get response"""
        try:
            self._update_token_tracking()
            
            messages = [
                {"role": "system", "content": self.basic_prompt},
                {"role": "user", "content": user_message},
            ]

            completion = self.client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=messages
            )
            
            answer = completion.choices[0].message.content
            self._update_token_count(completion.usage.total_tokens)
            
            return answer
            
        except Exception as e:
            handle_error(logger, e, "Groq API request")
            return "I apologize, but I encountered an error processing your request."

    def _update_token_tracking(self):
        """Update token tracking and rotate API key if needed"""
        try:
            if self.start_time is None:
                self.start_time = time.time()

            elapsed_time = time.time() - self.start_time
            
            if elapsed_time > 60:
                self.reset_token_count()
                self.start_time = time.time()

            if self.token_count >= 6000:
                self.rotate_api_key()
                self.reset_token_count()
                self.start_time = time.time()
        except Exception as e:
            handle_error(logger, e, "Token tracking update", silent=True)

    def _update_token_count(self, tokens):
        """Update token count and log"""
        self.token_count += tokens
        logger.info(f"Total tokens in rotation: {self.token_count}")