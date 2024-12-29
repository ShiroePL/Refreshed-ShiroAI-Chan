from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class ChatRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def save_message(self, user_id: str, content: str, role: str = "user") -> bool:
        """Adapted from your insert_message_to_db function"""
        try:
            query = text("""
                INSERT INTO user_messages (user_id, content, role, added_time)
                VALUES (:user_id, :content, :role, NOW())
            """)
            
            await self.session.execute(query, {
                "user_id": user_id,
                "content": content,
                "role": role
            })
            await self.session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error saving message: {e}")
            await self.session.rollback()
            return False
    
    async def get_user_history(self, user_id: str, limit: int = 30) -> List[Dict]:
        """Adapted from your get_messages_from_db function"""
        try:
            query = text("""
                SELECT id, content, role, added_time
                FROM user_messages
                WHERE user_id = :user_id
                ORDER BY added_time DESC
                LIMIT :limit
            """)
            
            result = await self.session.execute(query, {
                "user_id": user_id,
                "limit": limit
            })
            
            messages = []
            for row in result.mappings():
                messages.append({
                    "id": row.id,
                    "content": row.content,
                    "role": row.role,
                    "timestamp": row.added_time.isoformat()
                })
            
            return messages
            
        except Exception as e:
            logger.error(f"Error fetching messages: {e}")
            return []
    
    async def delete_user_history(self, user_id: str) -> bool:
        """Adapted from your delete_messages function"""
        try:
            query = text("""
                DELETE FROM user_messages
                WHERE user_id = :user_id
            """)
            
            await self.session.execute(query, {"user_id": user_id})
            await self.session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error deleting messages: {e}")
            await self.session.rollback()
            return False 