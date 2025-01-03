from typing import Optional, Dict, Union, List
from datetime import datetime
from openai import AsyncOpenAI
import os
from modules.ai.services.prompt_builder import PromptBuilder
import httpx
from src.config.service_config import DB_MODULE_URL
from src.utils.logging_config import setup_logger

logger = setup_logger("openai_service")

class OpenAIService:
    def __init__(self):
        # Get API key directly from environment variable
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("No OPENAI_API_KEY environment variable found")
            
        logger.info(f"Initializing OpenAIService with API key: {api_key[:4]}...{api_key[-4:]}")
        self.client = AsyncOpenAI(api_key=api_key)
        self.prompt_builder = PromptBuilder()
        self.error_count = 0
        self.last_error_time = None
        self.backoff_time = 1  # Start with 1 second backoff
        logger.info("OpenAI service initialized successfully")
        
    async def send_to_openai(self, 
                            user_message: str,
                            vector_db_service=None,
                            chat_history_service=None,
                            context_manager=None) -> str:
        """Send a message to OpenAI API with dynamically built prompt"""
        try:
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

            # Log start time
            start_time = datetime.now()
            logger.info(f"[OPENAI] Starting API call at {start_time.strftime('%H:%M:%S.%f')[:-3]}")

            completion = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7,
                max_tokens=1000,
            )

            # Log end time and calculate duration
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            logger.info(f"[OPENAI] API call completed at {end_time.strftime('%H:%M:%S.%f')[:-3]}")
            logger.info(f"[OPENAI] Total API call duration: {duration:.3f} seconds")
            
            # Reset error count on successful request
            self.error_count = 0
            self.backoff_time = 1
            
            answer = completion.choices[0].message.content
            
            # Log token usage
            logger.info(f"[OPENAI] Tokens used - Prompt: {completion.usage.prompt_tokens}, "
                       f"Completion: {completion.usage.completion_tokens}, "
                       f"Total: {completion.usage.total_tokens}")
            
            # Log the response length
            logger.info(f"[OPENAI] Received response ({len(answer)} chars): {answer[:30]}...")
            
            # Save the exchange to DB
            await self._save_chat_exchange(user_message, answer)
            
            return answer
            
        except Exception as e:
            self._handle_api_error(e)
            logger.error(f"[OPENAI] API Error: {str(e)}")
            return "I apologize, but I encountered a temporary issue. Please try again in a moment."

    def _should_backoff(self) -> bool:
        """Check if we should back off based on recent errors"""
        if not self.last_error_time:
            return False
            
        time_since_error = (datetime.now() - self.last_error_time).total_seconds()
        return time_since_error < self.backoff_time

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
        
        logger.error(f"[OPENAI] API Error (Count: {self.error_count}): {str(error)}")
        logger.info(f"[OPENAI] Backing off for {self.backoff_time} seconds") 