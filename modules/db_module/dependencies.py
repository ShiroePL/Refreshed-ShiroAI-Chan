from typing import Optional, List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from modules.db_module.models import ContextChoice
from modules.db_module.database import async_session_maker
from src.utils.logging_config import setup_logger

from typing import AsyncGenerator
from datetime import datetime

logger = setup_logger("db_dependencies")


async def get_active_context() -> Optional[str]:
    start_time = datetime.now()
    logger.info("[CONTEXT] Starting database query for active context")
    async with async_session_maker() as session:
        query = select(ContextChoice).where(ContextChoice.is_active == True)
        query_start = datetime.now()
        result = await session.execute(query)
        query_duration = (datetime.now() - query_start).total_seconds()
        logger.info(f"[CONTEXT] Database query executed in {query_duration:.3f} seconds")
        
        context = result.scalar_one_or_none()
        total_duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"[CONTEXT] Total context retrieval completed in {total_duration:.3f} seconds")
        return context.context_text if context else None

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides an async database session.
    """
    logger.debug("[DB] Creating new database session")
    try:
        async_session = async_session_maker()
        logger.debug("[DB] Database session created successfully")
        try:
            yield async_session
        finally:
            logger.debug("[DB] Closing database session")
            await async_session.close()
    except Exception as e:
        logger.error(f"[DB] Error in database session: {e}")
        raise 

async def save_context(context_text: str) -> bool:
    async with async_session_maker() as session:
        try:
            # First, set all contexts to inactive
            await session.execute(
                update(ContextChoice).values(is_active=False)
            )
            
            # Create new context
            new_context = ContextChoice(
                context_text=context_text,
                is_active=True
            )
            session.add(new_context)
            await session.commit()
            return True
        except Exception as e:
            await session.rollback()
            raise e 

async def get_available_contexts() -> List[Dict]:
    """Get all available contexts"""
    async with async_session_maker() as session:
        query = select(ContextChoice).order_by(ContextChoice.created_at.desc())
        result = await session.execute(query)
        contexts = result.scalars().all()
        return [
            {
                "id": ctx.id,
                "text": ctx.context_text,
                "is_active": ctx.is_active,
                "created_at": ctx.created_at.isoformat()
            }
            for ctx in contexts
        ]

async def set_active_context(context_id: int) -> bool:
    """Set a context as active"""
    async with async_session_maker() as session:
        try:
            # First, set all contexts to inactive
            await session.execute(
                update(ContextChoice).values(is_active=False)
            )
            
            # Set the selected context as active
            await session.execute(
                update(ContextChoice)
                .where(ContextChoice.id == context_id)
                .values(is_active=True)
            )
            
            await session.commit()
            return True
        except Exception as e:
            await session.rollback()
            logger.error(f"[CONTEXT] Error setting active context: {e}")
            return False 