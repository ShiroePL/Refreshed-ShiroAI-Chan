from fastapi import APIRouter, Depends, HTTPException
from modules.db_module.services.chat_service import ChatService
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict
from modules.db_module.dependencies import get_db_session
from src.utils.logging_config import setup_logger

logger = setup_logger("db_router")

router = APIRouter()

@router.get("/chat/exchange")
async def get_chat_history(
    limit: int = 30,
    session: AsyncSession = Depends(get_db_session)
) -> List[Dict]:
    logger.info(f"[GET] Received request for chat history. Limit: {limit}")
    try:
        service = ChatService(session)
        messages = await service.get_chat_history(limit)
        logger.info(f"[GET] Retrieved {len(messages)} messages from history")
        return messages
    except Exception as e:
        logger.error(f"[GET] Error retrieving chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/exchange")
async def save_chat_exchange(
    question: str,
    answer: str,
    session: AsyncSession = Depends(get_db_session)
) -> Dict:
    logger.info("[POST] Received chat exchange to save")
    try:
        service = ChatService(session)
        success = await service.save_exchange(question, answer)
        if not success:
            logger.error("[POST] Failed to save chat exchange")
            raise HTTPException(status_code=500, detail="Failed to save chat exchange")
        logger.info("[POST] Successfully saved chat exchange")
        return {"status": "success"}
    except Exception as e:
        logger.error(f"[POST] Error saving chat exchange: {e}")
        raise

@router.post("/chat/usage")
async def save_token_usage(
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
    session: AsyncSession = Depends(get_db_session)
) -> Dict:
    service = ChatService(session)
    success = await service.save_token_usage(prompt_tokens, completion_tokens, total_tokens)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save token usage")
    return {"status": "success"} 