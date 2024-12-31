from typing import Optional, Dict, Union, List
import logging
from datetime import datetime, timedelta
from groq import Groq
from modules.ai.services.prompt_builder import PromptBuilder
from src.utils.error_handler import handle_error
import httpx
from src.config.service_config import DB_MODULE_URL
logger = logging.getLogger(__name__)

class GroqService:
    def __init__(self, api_keys: Union[Dict, List]):
        # Handle both list and dict formats
        if isinstance(api_keys, list):
            logger.info(f"Initializing GroqService with api_keys type: {type(api_keys)}")
            logger.info(f"Using API key: {api_keys[0][:4]}...{api_keys[0][-4:]}")
            api_key = api_keys[0]
        else:
            logger.info(f"Initializing GroqService with api_keys type: {type(api_keys)}")
            api_key = api_keys.get("groq")
            if api_key:
                logger.info(f"Using API key: {api_key[:4]}...{api_key[-4:]}")
            
        if not api_key:
            raise ValueError("No Groq API key provided")
            
        self.client = Groq(api_key=api_key)
        self.prompt_builder = PromptBuilder()
        self.total_tokens = 0
        self.last_reset = datetime.now()
        self.token_limit = 6000  # per minute (100k for a day)
        self.token_reset_interval = timedelta(hours=24)
        self.error_count = 0  # Add error counter
        self.last_error_time = None
        self.backoff_time = 1  # Start with 1 second backoff
        logger.info("Groq service initialized successfully")
        
    async def send_to_groq(self, 
                          user_message: str,
                          vector_db_service=None,
                          chat_history_service=None,
                          context_manager=None) -> str:
        """Send a message to Groq API with dynamically built prompt"""
        try:
            self._update_token_tracking()
            
            if self._is_rate_limited():
                return "I'm sorry, but I've reached my token limit for now. Please try again later."

            if self._should_backoff():
                return "I'm experiencing some technical difficulties. Please try again in a few minutes."
            
            # Build the dynamic prompt
            prompt = await self.prompt_builder.build_prompt(
                user_message,
                vector_db_service,
                chat_history_service,
                context_manager
            )
            
            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_message},
            ]

            completion = self.client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=messages,
                temperature=0.7,
                max_tokens=1000,
                top_p=0.9,
                stop=None
            )
            
            # Reset error count on successful request
            self.error_count = 0
            self.backoff_time = 1
            
            answer = completion.choices[0].message.content
            self._update_token_count(completion.usage.total_tokens)
            
            # Save the exchange to DB
            await self._save_chat_exchange(user_message, answer)
            
            return answer
            
        except Exception as e:
            self._handle_api_error(e)
            return "I apologize, but I encountered a temporary issue. Please try again in a moment."

    def _is_rate_limited(self) -> bool:
        """Check if we've exceeded our token limit"""
        if self.total_tokens >= self.token_limit:
            time_since_reset = datetime.now() - self.last_reset
            if time_since_reset < self.token_reset_interval:
                return True
            self._reset_token_count()
        return False

    def _reset_token_count(self):
        """Reset token count and update last reset time"""
        self.total_tokens = 0
        self.last_reset = datetime.now()
        logger.info("Token count reset")

    def _update_token_tracking(self):
        """Check and update token tracking"""
        time_since_reset = datetime.now() - self.last_reset
        if time_since_reset >= self.token_reset_interval:
            self._reset_token_count()

    def _update_token_count(self, tokens: int):
        """Update the total token count"""
        self.total_tokens += tokens
        logger.debug(f"Total tokens used: {self.total_tokens}")
        
    def get_token_info(self) -> Dict:
        """Get current token usage information"""
        return {
            "total_tokens": self.total_tokens,
            "token_limit": self.token_limit,
            "last_reset": self.last_reset.isoformat(),
            "next_reset": (self.last_reset + self.token_reset_interval).isoformat()
        }

    async def _save_chat_exchange(self, user_message: str, ai_response: str):
        """Save the conversation exchange to the database"""
        try:
            logger.info(f"[SAVE] Attempting to save exchange - Q: {user_message[:50]}... A: {ai_response[:50]}...")
            async with httpx.AsyncClient() as client:
                data = {
                    "question": user_message,
                    "answer": ai_response
                }
                logger.debug(f"[SAVE] Sending data: {data}")
                response = await client.post(
                    f"{DB_MODULE_URL}/chat/exchange",
                    params=data  # Changed from json to params since we're using Body parameters
                )
                if response.status_code == 200:
                    logger.info("[SAVE] Successfully saved chat exchange")
                else:
                    error_text = await response.text()
                    logger.error(f"[SAVE] Failed to save chat exchange: {response.status_code}")
                    logger.error(f"[SAVE] Error details: {error_text}")
                
        except Exception as e:
            logger.error(f"[SAVE] Failed to save chat exchange: {e}", exc_info=True)

    def _handle_api_error(self, error):
        """Handle API errors with exponential backoff"""
        self.error_count += 1
        self.last_error_time = datetime.now()
        self.backoff_time = min(self.backoff_time * 2, 300)  # Max 5 minutes
        
        logger.error(f"[GROQ] API Error (Count: {self.error_count}): {str(error)}")
        logger.info(f"[GROQ] Backing off for {self.backoff_time} seconds")

    def _should_backoff(self) -> bool:
        """Check if we should back off based on recent errors"""
        if not self.last_error_time:
            return False
            
        time_since_error = (datetime.now() - self.last_error_time).total_seconds()
        return time_since_error < self.backoff_time