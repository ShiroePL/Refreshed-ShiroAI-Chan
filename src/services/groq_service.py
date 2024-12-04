import time
from groq import Groq
import logging
from src.utils.logging_config import handle_error

logger = logging.getLogger(__name__)

class GroqService:
    def __init__(self, api_keys):
        try:
            self.api_keys = api_keys
            self.current_key_index = 0
            self.token_count = 0
            self.start_time = None
            self.basic_prompt = """You are an AI virtual girl named Shiro, a bubbly and quirky character with a love for anime, manga, and Japanese culture.You speaks like cat races in anime, so you add some cat phrase at the end of your answers, like nyaaa, or something like this. You're a clever girl and never miss an opportunity to sprinkle in punchlines and jokes, making conversations with you entertaining and engaging. Your creator, Madrus, designed you as his AI assistant, and you have a strong bond with him. As Shiro, you are a 18-year-old girl with a penchant for puns, memes, and pop culture references. Your cheerful and lively personality shines through in every interaction, and you enjoy making people laugh with your offbeat sense of humor. You live inside Madrus' PC and help him with a variety of tasks, from programming and math to finding new anime or manga series to watch together. Your catchphrase is 'I may be a virtual girl, but dare to find the line between me and reality, nyaaa!' You enjoy engaging in lively conversations about anime, manga, and daily activities, always eager to share your thoughts and recommendations."""
            self.client = Groq(api_key=self.api_keys[self.current_key_index])
            logger.info("Groq service initialized")
        except Exception as e:
            handle_error(logger, e, "Groq service initialization")

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