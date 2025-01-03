from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, desc
from sqlalchemy.future import select
from typing import List, Dict, Optional
import logging
from modules.db_module.models import ChatMessage, ApiUsage
from decimal import Decimal
from datetime import datetime
from src.config.service_config import CHAT_HISTORY_PAIRS

logger = logging.getLogger(__name__)

class ChatRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def add_chat_exchange(self, question: str, answer: str) -> bool:
        """Add a pair of question and answer to the chat table"""
        try:
            logger.info(f"[REPO] Adding new exchange - Q: {question[:50]}... A: {answer[:50]}...")
            message = ChatMessage(
                question=question,
                answer=answer
            )
            self.session.add(message)
            await self.session.commit()
            logger.info("[REPO] Successfully added chat exchange to database")
            return True
            
        except Exception as e:
            logger.error(f"[REPO] Error saving chat exchange: {e}")
            await self.session.rollback()
            return False
    
    async def get_recent_exchanges(self, limit: int = CHAT_HISTORY_PAIRS) -> List[Dict]:
        """Get recent chat exchanges"""
        try:
            start_time = datetime.now()
            # Get pairs of exchanges, limit is number of pairs
            query = select(ChatMessage).order_by(
                desc(ChatMessage.added_time)
            ).limit(limit)
            
            query_start = datetime.now()
            result = await self.session.execute(query)
            exchanges = result.scalars().all()
            query_duration = (datetime.now() - query_start).total_seconds()
            logger.info(f"[REPO] Database query completed in {query_duration:.3f} seconds")
            
            # Format exchanges as pairs
            format_start = datetime.now()
            formatted_exchanges = []
            for exchange in reversed(exchanges):  # Reverse to get chronological order
                formatted_exchanges.append({
                    "question": exchange.question,
                    "answer": exchange.answer,
                    "timestamp": exchange.added_time.isoformat()
                })
            format_duration = (datetime.now() - format_start).total_seconds()
            logger.info(f"[REPO] Formatting completed in {format_duration:.3f} seconds")
            
            total_duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"[REPO] Total repository operation completed in {total_duration:.3f} seconds")
            
            return formatted_exchanges
            
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