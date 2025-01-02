from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from modules.db_module.services.vector_store import VectorStoreService
from modules.db_module.database import db_engine, async_session_maker
from modules.db_module.services.chat_service import ChatService
from src.utils.logging_config import setup_logger
import platform
import uvicorn
from .dependencies import save_context, get_active_context
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from modules.db_module.services.cache_service import ChatHistoryCache
from src.config.service_config import CHAT_HISTORY_PAIRS

logger = setup_logger("db_module_main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        logger.info("[STARTUP] Initializing DB module services...")
        
        # Initialize Vector Store Service
        app.state.vector_store = VectorStoreService()
        logger.info("[INIT] Vector store service initialized")
        
        # Initialize chat history cache
        app.state.chat_cache = ChatHistoryCache()
        # Load initial history
        async with async_session_maker() as session:
            chat_service = ChatService(session)
            initial_history = await chat_service.get_chat_history(limit=CHAT_HISTORY_PAIRS)
            app.state.chat_cache.update_cache(initial_history)
        logger.info(f"[INIT] Chat history cache initialized with {CHAT_HISTORY_PAIRS} pairs")
        
        yield
        
        # Cleanup
        await db_engine.dispose()
        logger.info("[SHUTDOWN] Database connections closed")
        
    except Exception as e:
        logger.error(f"[ERROR] Failed to initialize DB module: {e}")
        raise

app = FastAPI(lifespan=lifespan)

# Import routers here to avoid circular imports
from modules.db_module.routers.chat_history import router as chat_router
from modules.db_module.routers.vector_store import router as vector_router

# Include routers
app.include_router(vector_router, prefix="/vector", tags=["vector"])
app.include_router(chat_router, tags=["chat"])

logger.info(f"[INIT] Registered routes: {[route.path for route in app.routes]}")

# Add these new endpoints
class ContextUpdate(BaseModel):
    context_text: str

@app.post("/context/update")
async def update_context(context: ContextUpdate):
    try:
        await save_context(context.context_text)
        return {"status": "success", "message": "Context updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/context/current")
async def get_current_context():
    try:
        context = await get_active_context()
        return {"context": context or "No context set"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Add this after creating the FastAPI app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5000", "http://127.0.0.1:5000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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