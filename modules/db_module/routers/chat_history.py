from fastapi import APIRouter, Depends, HTTPException, Form, BackgroundTasks, Request
from pydantic import BaseModel
from modules.db_module.services.chat_service import ChatService
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict
from modules.db_module.dependencies import get_db_session
from src.utils.logging_config import setup_logger
from modules.db_module.services.cache_service import ChatHistoryCache
from src.config.service_config import CHAT_HISTORY_PAIRS
from datetime import datetime

logger = setup_logger("db_router")

router = APIRouter()

async def save_exchange_background(service: ChatService, question: str, answer: str):
    """Background task for saving chat exchange"""
    try:
        await service.save_exchange(question, answer)
        logger.info("[BACKGROUND] Successfully saved chat exchange")
    except Exception as e:
        logger.error(f"[BACKGROUND] Error saving chat exchange: {e}", exc_info=True)

@router.get("/chat/exchange")
async def get_chat_history(
    request: Request,
    limit: int = CHAT_HISTORY_PAIRS,
    session: AsyncSession = Depends(get_db_session)
) -> List[Dict]:
    start_time = datetime.now()
    logger.info(f"[GET] Received request for chat history. Limit: {limit}")
    try:
        # Use cache from app state
        cache = request.app.state.chat_cache
        cached_messages = cache.get_cached_history()
        
        # If requesting same or fewer messages than what's cached, return from cache
        if limit <= CHAT_HISTORY_PAIRS:
            cache_duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"[GET] Retrieved {len(cached_messages)} messages from cache in {cache_duration:.3f} seconds")
            return cached_messages
            
        # Only hit DB if requesting more than cached amount
        db_start = datetime.now()
        service = ChatService(session)
        messages = await service.get_chat_history(limit)
        db_duration = (datetime.now() - db_start).total_seconds()
        logger.info(f"[GET] Retrieved {len(messages)} messages from DB in {db_duration:.3f} seconds")
        
        total_duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"[GET] Total request duration: {total_duration:.3f} seconds")
        return messages
        
    except Exception as e:
        logger.error(f"[GET] Error retrieving chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/exchange")
async def save_chat_exchange(
    request: Request,
    background_tasks: BackgroundTasks,
    question: str,
    answer: str,
    session: AsyncSession = Depends(get_db_session)
) -> Dict:
    logger.info(f"[POST] Received chat exchange to save - Q: {question[:50]}...")
    try:
        # Use cache from app state
        cache = request.app.state.chat_cache
        cache.add_new_exchange(question, answer)
        
        # Save to DB in background
        service = ChatService(session)
        background_tasks.add_task(save_exchange_background, service, question, answer)
        logger.info("[POST] Added chat exchange to background tasks")
        return {"status": "processing"}
    except Exception as e:
        logger.error(f"[POST] Error queuing chat exchange: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

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