import time
from typing import Optional, Dict, Union, List
import logging
from datetime import datetime, timedelta
from groq import Groq
from modules.ai.services.prompt_builder import PromptBuilder
from src.utils.error_handler import handle_error
import httpx
from src.config.service_config import DB_MODULE_URL
from src.utils.logging_config import setup_logger

logger = setup_logger("ai_service")

class GroqService:
    def __init__(self, api_keys: Union[Dict, List]):
        logger.info(f"Initializing GroqService with api_keys type: {type(api_keys)}")
        
        # Initialize key management
        self.free_tier_keys = []
        self.paid_tier_key = None
        
        # Initialize prompt builder
        self.prompt_builder = PromptBuilder()
        
        # Handle both list and dict formats
        if isinstance(api_keys, dict):
            self.free_tier_keys = [api_keys.get("madruss_groq_key"), api_keys.get("otaku_groq_key")]
            self.paid_tier_key = api_keys.get("paid_groq_key")
        else:
            # Assuming the list is ordered: [madruss_key, otaku_key, paid_key]
            self.free_tier_keys = api_keys[:2]
            self.paid_tier_key = api_keys[2] if len(api_keys) > 2 else None
        
        # Remove any None values
        self.free_tier_keys = [k for k in self.free_tier_keys if k]
        
        if not self.free_tier_keys:
            raise ValueError("No valid Groq API keys provided")
        
        # Initialize with default key (madruss_key)
        self.current_key = self.free_tier_keys[0]
        self.current_key_index = 0
        self.client = Groq(api_key=self.current_key)
        
        # Token tracking
        self.token_count = 0
        self.last_reset = datetime.now()
        self.token_reset_interval = timedelta(minutes=1)  # Reset every minute
        self.token_limit = 6000  # Free tier limit
        
        # Error handling attributes
        self.error_count = 0
        self.last_error_time = None
        self.backoff_time = 1
        
        logger.info(f"Using API key: {self.current_key[:4]}...{self.current_key[-4:]}")
        logger.info("Groq service initialized successfully")

    def _rotate_to_next_free_key(self):
        """Rotate to the next available free tier key"""
        prev_key = self.current_key
        self.current_key_index = (self.current_key_index + 1) % len(self.free_tier_keys)
        self.current_key = self.free_tier_keys[self.current_key_index]
        self.client = Groq(api_key=self.current_key)
        self.token_count = 0  # Reset token count for new key
        self.last_reset = datetime.now()
        logger.info(f"Rotated from key {prev_key[:4]}...{prev_key[-4:]} to {self.current_key[:4]}...{self.current_key[-4:]}")

    def _switch_to_paid_key(self):
        """Switch to paid tier key if available"""
        if self.paid_tier_key:
            self.current_key = self.paid_tier_key
            self.client = Groq(api_key=self.current_key)
            self.token_limit = 30000  # Paid tier limit
            logger.info("Switched to paid tier key")
            return True
        return False

    async def send_to_groq(self, user_message: str, **kwargs) -> str:
        """Send a message to Groq API with token limit handling and key rotation"""
        try:
            # Check if we should reset token count
            if datetime.now() - self.last_reset >= self.token_reset_interval:
                self.token_count = 0
                self.last_reset = datetime.now()
                logger.info("Reset token count due to time interval")
            
            # Check if we're over the limit and should rotate
            if self.token_count >= self.token_limit:
                logger.warning(f"Token count {self.token_count} exceeds limit {self.token_limit}, rotating key")
                self._rotate_to_next_free_key()
            
            # Build the dynamic prompt
            prompt = await self.prompt_builder.build_prompt(
                user_message,
                **kwargs
            )
            
            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_message},
            ]
            
            try:
                completion = self.client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1000
                )
                
                # Update token count
                total_tokens = completion.usage.total_tokens
                self.token_count += total_tokens
                logger.info(f"Total tokens in current minute: {self.token_count} (Key: {self.current_key[:4]}...{self.current_key[-4:]})")
                
                answer = completion.choices[0].message.content
                
                # Save the chat exchange
                await self._save_chat_exchange(user_message, answer)
                return answer
                
            except Exception as e:
                error_str = str(e).lower()
                if "429" in error_str or "rate_limit_exceeded" in error_str:
                    logger.warning(f"Rate limit exceeded on key {self.current_key[:4]}...{self.current_key[-4:]}")
                    
                    # Try rotating to next free key
                    self._rotate_to_next_free_key()
                    logger.info(f"Retrying with new key: {self.current_key[:4]}...{self.current_key[-4:]}")
                    
                    # Retry with new key
                    try:
                        completion = self.client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=messages,
                            temperature=0.7,
                            max_tokens=1000
                        )
                        answer = completion.choices[0].message.content
                        await self._save_chat_exchange(user_message, answer)
                        return answer
                        
                    except Exception as e2:
                        error_str2 = str(e2).lower()
                        # If still hitting limits, try paid key
                        if ("429" in error_str2 or "rate_limit_exceeded" in error_str2) and self._switch_to_paid_key():
                            logger.info("Attempting paid tier key after exhausting free keys")
                            completion = self.client.chat.completions.create(
                                model="llama-3.3-70b-versatile",
                                messages=messages,
                                temperature=0.7,
                                max_tokens=1000
                            )
                            answer = completion.choices[0].message.content
                            await self._save_chat_exchange(user_message, answer)
                            return answer
                        
                        raise e2
                raise e
            
            
                
        except Exception as e:
            logger.error(f"Error in send_to_groq: {str(e)}")
            return "I apologize, but I encountered an error processing your request."

    def get_token_info(self) -> Dict:
        """Get current token usage information"""
        return {
            "total_tokens": self.token_count,
            "token_limit": self.token_limit,
            "last_reset": self.last_reset.isoformat(),
            "next_reset": (self.last_reset + self.token_reset_interval).isoformat()
        }

    async def _save_chat_exchange(self, user_message: str, ai_response: str):
        """Save the conversation exchange to the database"""
        try:
            logger.info(f"[SAVE] Queuing exchange save - Q: {user_message[:50]}... A: {ai_response[:50]}...")
            async with httpx.AsyncClient() as client:
                data = {
                    "question": user_message,
                    "answer": ai_response
                }
                logger.debug(f"[SAVE] Sending data: {data}")
                response = await client.post(
                    f"{DB_MODULE_URL}/chat/exchange",
                    params=data
                )
                if response.status_code == 200:
                    logger.info("[SAVE] Successfully queued chat exchange")
                else:
                    error_text = await response.text()
                    logger.error(f"[SAVE] Failed to queue chat exchange: {response.status_code}")
                    logger.error(f"[SAVE] Error details: {error_text}")
                
        except Exception as e:
            logger.error(f"[SAVE] Failed to queue chat exchange: {e}", exc_info=True)

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