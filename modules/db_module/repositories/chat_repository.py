from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, desc
from sqlalchemy.future import select
from typing import List, Dict, Optional
import logging
from ..models import ChatMessage, ApiUsage
from decimal import Decimal

logger = logging.getLogger(__name__)

class ChatRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def add_chat_exchange(self, question: str, answer: str) -> bool:
        """Add a pair of question and answer to the chat table"""
        try:
            message = ChatMessage(
                question=question,
                answer=answer
            )
            self.session.add(message)
            await self.session.commit()
            logger.info("Added chat exchange to database")
            return True
            
        except Exception as e:
            logger.error(f"Error saving chat exchange: {e}")
            await self.session.rollback()
            return False
    
    async def get_recent_exchanges(self, limit: int = 30) -> List[Dict]:
        """Get recent chat exchanges"""
        try:
            query = select(ChatMessage).order_by(
                desc(ChatMessage.added_time)
            ).limit(limit)
            
            result = await self.session.execute(query)
            exchanges = result.scalars().all()
            
            # Add logging to see what we got from DB
            for ex in exchanges:
                logger.info(
                    f"[REPO] DB Result - ID: {ex.id}, "
                    f"Question: {ex.question[:50] + '...' if ex.question else None}, "
                    f"Answer: {ex.answer[:50] + '...' if ex.answer else None}, "
                    f"Time: {ex.added_time}"
                )
            
            return [
                {
                    "question": exchange.question,
                    "answer": exchange.answer,
                    "timestamp": exchange.added_time.isoformat()
                }
                for exchange in exchanges
            ]
            
        except Exception as e:
            logger.error(f"Error fetching chat history: {e}")
            return []
    
    async def save_api_usage(self, prompt_tokens: int, completion_tokens: int, total_tokens: int) -> bool:
        """Save API usage statistics"""
        try:
            usage = ApiUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens
            )
            self.session.add(usage)
            await self.session.commit()
            
            # Calculate total usage and cost
            query = select(func.sum(ApiUsage.total_tokens))
            result = await self.session.execute(query)
            token_sum = result.scalar() or 0
            
            # Calculate cost (using your existing formula)
            token_sum = Decimal(str(token_sum))
            price_per_1000_tokens = Decimal('0.002')
            tokens_per_dollar = Decimal('1000')
            price = token_sum / tokens_per_dollar * price_per_1000_tokens
            
            logger.info(f"Total tokens used: {token_sum}, Current cost: ${price}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving API usage: {e}")
            await self.session.rollback()
            return False 