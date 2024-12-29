from modules.db_module.repositories.chat_repository import ChatRepository
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Optional

class ChatHistoryService:
    def __init__(self, session: AsyncSession):
        self.repository = ChatRepository(session)
    
    async def get_recent_messages(self, user_id: str, limit: int = 30) -> List[Dict]:
        return await self.repository.get_user_history(user_id, limit)
    
    async def save_message(self, user_id: str, content: str, role: str = "user") -> bool:
        return await self.repository.save_message(user_id, content, role)
    
    async def clear_history(self, user_id: str) -> bool:
        return await self.repository.delete_user_history(user_id) 