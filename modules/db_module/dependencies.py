from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.utils.logging_config import setup_logger
from modules.db_module.database import async_session_maker

logger = setup_logger("db_dependencies")

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