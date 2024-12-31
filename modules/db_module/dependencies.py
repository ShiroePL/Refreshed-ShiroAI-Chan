from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from modules.db_module.models import ContextChoice
from modules.db_module.database import async_session_maker
from src.utils.logging_config import setup_logger

from typing import AsyncGenerator

logger = setup_logger("db_dependencies")


async def get_active_context() -> Optional[str]:
    async with async_session_maker() as session:
        query = select(ContextChoice).where(ContextChoice.is_active == True)
        result = await session.execute(query)
        context = result.scalar_one_or_none()
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