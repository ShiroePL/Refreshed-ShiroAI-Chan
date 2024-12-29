from fastapi import APIRouter, Depends, HTTPException
from ..services.mariadb import ChatHistoryService
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict
from ..dependencies import get_db_session

router = APIRouter()

@router.get("/chat/history/{user_id}")
async def get_chat_history(
    user_id: str,
    limit: int = 30,
    session: AsyncSession = Depends(get_db_session)
) -> List[Dict]:
    service = ChatHistoryService(session)
    messages = await service.get_recent_messages(user_id, limit)
    return messages

@router.post("/chat/message")
async def save_chat_message(
    user_id: str,
    content: str,
    role: str = "user",
    session: AsyncSession = Depends(get_db_session)
) -> Dict:
    service = ChatHistoryService(session)
    success = await service.save_message(user_id, content, role)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save message")
    return {"status": "success"}

@router.delete("/chat/history/{user_id}")
async def clear_chat_history(
    user_id: str,
    session: AsyncSession = Depends(get_db_session)
) -> Dict:
    service = ChatHistoryService(session)
    success = await service.clear_history(user_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to clear history")
    return {"status": "success"} 