from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager
from modules.db_module.services.vector_store import VectorStoreService
from src.config import api_keys
from src.utils.logging_config import setup_logger
import platform
import uvicorn
from modules.db_module.routers import vector_store

logger = setup_logger("db_module_main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # Initialize DB connections
        app.state.db_engine = create_async_engine(
            f"mysql+aiomysql://{api_keys.user_name}:{api_keys.db_password}@{api_keys.host_name}/{api_keys.db_name}",
            pool_pre_ping=True,
            pool_size=20,
            max_overflow=10
        )
        
        app.state.async_session = sessionmaker(
            app.state.db_engine, class_=AsyncSession, expire_on_commit=False
        )
        
        # Initialize Vector Store Service
        app.state.vector_store = VectorStoreService()
        logger.info("[INIT] Vector store service initialized")
        
        yield
        
        # Cleanup
        await app.state.db_engine.dispose()
        
    except Exception as e:
        logger.error(f"Error initializing DB module: {e}")
        raise

app = FastAPI(lifespan=lifespan)

# Include routers
app.include_router(vector_store.router, prefix="/vector", tags=["vector"])

if __name__ == "__main__":
    logger.info("[STARTUP] Starting DB service...")
    
    config = {
        "host": "127.0.0.1",
        "port": 8014,  # Different port from AI service
        "loop": "asyncio",
        "ws_ping_interval": 20,
        "ws_ping_timeout": 20,
        "log_level": "warning",
    }
    
    if platform.system() == "Windows":
        logger.info("[INIT] Configuring for Windows environment")
        config.update({
            "workers": 1,
            "http": "h11",
            "ws": "wsproto"
        })
    else:
        logger.info("[INIT] Configuring for Unix environment")
        config.update({
            "workers": 4,
            "loop": "uvloop",
            "http": "httptools",
            "ws": "websockets"
        })
    
    logger.info(f"[STARTUP] Starting server with config: {config}")
    
    # Use Server instance for more control
    server = uvicorn.Server(uvicorn.Config(
        app,
        **config
    ))
    server.run() 