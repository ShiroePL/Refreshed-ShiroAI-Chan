import time
from groq import Groq
import logging

logger = logging.getLogger(__name__)

class GroqService:
    def __init__(self, api_keys):
        self.api_keys = api_keys
        self.current_key_index = 0
        self.client = Groq(api_key=self.api_keys[self.current_key_index])
        self.token_count = 0
        self.start_time = None
        self.basic_prompt = """You are a helpful AI assistant named Shiro. You are friendly, 
        knowledgeable, and always eager to help. You provide clear and concise responses."""

    def reset_token_count(self):
        self.token_count = 0
        self.start_time = None

    def rotate_api_key(self):
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        self.client = Groq(api_key=self.api_keys[self.current_key_index])
        logger.debug(f"Rotated API key to: {self.current_key_index}")

    def send_to_groq(self, user_message):
        """Send a message to Groq API and get response"""
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

        messages = [
            {"role": "system", "content": self.basic_prompt},
            {"role": "user", "content": user_message},
        ]

        try:
            completion = self.client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=messages
            )
            
            answer = completion.choices[0].message.content
            total_tokens = completion.usage.total_tokens
            self.token_count += total_tokens
            
            logger.info(f"Total tokens in rotation: {self.token_count}")
            return answer
            
        except Exception as ex:
            logger.error(f"Error in send_to_groq: {ex}")
            return "I apologize, but I encountered an error processing your request." 