from typing import List, Dict, Optional
from modules.db_module.repositories.chat_repository import ChatRepository
from sqlalchemy.ext.asyncio import AsyncSession
from src.utils.logging_config import setup_logger

logger = setup_logger("db_service")

class ChatService:
    def __init__(self, session: AsyncSession):
        self.repository = ChatRepository(session)
        self.session = session  # Store session for background tasks
        logger.debug("[INIT] ChatService initialized")
    
    async def save_exchange(self, question: str, answer: str) -> bool:
        """Save a Q&A exchange to the database"""
        try:
            logger.debug(f"[SERVICE] Saving exchange - Q: {question[:50]}...")
            success = await self.repository.add_chat_exchange(question, answer)
            # Make sure to close the session after background task is done
            await self.session.close()
            return success
        except Exception as e:
            logger.error(f"[SERVICE] Error in save_exchange: {e}")
            await self.session.close()
            return False
    
    async def get_chat_history(self, limit: int = 30) -> List[Dict]:
        """Get recent chat history"""
        logger.info(f"[SERVICE] Fetching chat history. Limit: {limit}")
        try:
            messages = await self.repository.get_recent_exchanges(limit)
            # for msg in messages:
            #     logger.info(
            #         f"[SERVICE] Message - Question: {msg.get('question', '')[:30]}... "
            #         f"Answer: {msg.get('answer', '')[:30]}..."
            #     )
            return messages
        except Exception as e:
            logger.error(f"[SERVICE] Error fetching chat history: {e}")
            raise
    
    async def save_token_usage(self, prompt_tokens: int, completion_tokens: int, total_tokens: int) -> bool:
        """Save token usage statistics"""
        return await self.repository.save_api_usage(prompt_tokens, completion_tokens, total_tokens) 