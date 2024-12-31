from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.config import api_keys
from src.utils.logging_config import setup_logger

logger = setup_logger("db_database")

# Create global variables for database connections
db_engine = create_async_engine(
    f"mysql+aiomysql://{api_keys.user_name}:{api_keys.db_password}@{api_keys.host_name}/{api_keys.db_name}",
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=10
)

async_session_maker = sessionmaker(
    db_engine, class_=AsyncSession, expire_on_commit=False
) 