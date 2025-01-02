from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List
from dotenv import load_dotenv
import logging
import httpx
from datetime import datetime
import asyncio

from modules.ai.services.ai_service import GroqService
from modules.ai.services.tts_service import TTSService
from src.config.azure_config import get_groq_api_keys
from src.config.service_config import DB_MODULE_URL
import uvicorn
from contextlib import asynccontextmanager
from colorama import init
from src.utils.logging_config import setup_logger
from modules.ai.services.openai_service import OpenAIService
from src.config.service_config import CHAT_HISTORY_PAIRS

# Initialize colorama
init()

# Setup module-specific logger
logger = setup_logger('ai')

# Load environment variables
load_dotenv()

# Initialize services at startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        logger.info("[STARTUP] Initializing AI services...")
        
        # Load API keys
        app.state.api_keys = get_groq_api_keys()
        logger.info("[INIT] API keys loaded successfully")
        
        # Initialize Groq service
        app.state.groq_service = GroqService(app.state.api_keys)
        logger.info("[INIT] Groq service initialized")
        
        # Initialize TTS service
        app.state.tts_service = TTSService()
        logger.info("[INIT] TTS service initialized")
        
        # Initialize history service
        class HistoryService:
            async def get_chat_history(self, limit: int = 30) -> List[Dict]:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{DB_MODULE_URL}/chat/exchange",
                        params={"limit": limit}
                    )
                    if response.status_code == 200:
                        return response.json()
                    logger.error(f"Failed to fetch chat history: {response.status_code}")
                    return []
        
        app.state.history_service = HistoryService()
        logger.info("[INIT] History service initialized")
        
        # Initialize context manager (if needed)
        class ContextManager:
            async def get_current_context(self) -> str:
                return "No specific context"  # Or implement context logic
        
        app.state.context_manager = ContextManager()
        logger.info("[INIT] Context manager initialized")
        
        # Initialize OpenAI service
        app.state.openai_service = OpenAIService()
        logger.info("[INIT] OpenAI service initialized")
        
        logger.info("[SUCCESS] All services initialized successfully")
        yield
    except Exception as e:
        logger.error(f"[ERROR] Failed to initialize services: {e}", exc_info=True)
        raise
    finally:
        logger.info("[SHUTDOWN] Shutting down AI service")

app = FastAPI(lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add helper functions for parallel context gathering
async def get_vector_results(transcript: str) -> Dict:
    """Get relevant context from vector DB"""
    try:
        start_time = datetime.now()
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{DB_MODULE_URL}/vector/query",
                json={"query": transcript, "limit": 5}
            )
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"[VECTOR] Query completed in {duration:.3f} seconds")
            
            if response.status_code == 200:
                return response.json()
            logger.error(f"[VECTOR] Query failed with status {response.status_code}")
            logger.info("[VECTOR] Continuing without vector context")
            return None
    except Exception as e:
        logger.error(f"[VECTOR] Error getting vector results: {e}")
        logger.info("[VECTOR] Continuing without vector context")
        return None

async def get_chat_history() -> List[Dict]:
    """Get recent chat history"""
    try:
        start_time = datetime.now()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{DB_MODULE_URL}/chat/exchange",
                params={"limit": CHAT_HISTORY_PAIRS}
            )
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"[HISTORY] Fetch completed in {duration:.3f} seconds")
            
            if response.status_code == 200:
                return response.json()
            logger.error(f"[HISTORY] Fetch failed with status {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"[HISTORY] Error getting chat history: {e}")
        return []

async def get_context() -> str:
    """Get current context"""
    try:
        start_time = datetime.now()
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{DB_MODULE_URL}/context/current")
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"[CONTEXT] Fetch completed in {duration:.3f} seconds")
            
            if response.status_code == 200:
                return response.json().get('context', 'No specific context')
            logger.error(f"[CONTEXT] Fetch failed with status {response.status_code}")
            return "No specific context"
    except Exception as e:
        logger.error(f"[CONTEXT] Error getting current context: {e}")
        return "Error fetching context"

async def process_request(transcript: str, groq_service: GroqService, tts_service: TTSService, use_openai: bool = False, timings: dict = {}) -> Dict:
    """Process a single request through the AI pipeline"""
    try:
        logger.info(f"[RECEIVE] Processing request: {transcript[:30]}...")
        
        # Start timing vector/context gathering
        context_start = datetime.now()
        
        # Create tasks for parallel execution
        context_task = asyncio.create_task(get_context())
        history_task = asyncio.create_task(get_chat_history())
        
        # Try to get vector results, but don't let it block the whole process
        try:
            vector_task = asyncio.create_task(get_vector_results(transcript))
            vector_results, context, history = await asyncio.gather(
                vector_task,
                context_task,
                history_task
            )
        except Exception as e:
            logger.error(f"[VECTOR] Failed to get vector results: {e}")
            logger.info("[VECTOR] Proceeding without vector context")
            # Continue without vector results
            context, history = await asyncio.gather(
                context_task,
                history_task
            )
            vector_results = None
        
        # Record timing for context gathering
        context_duration = (datetime.now() - context_start).total_seconds()
        timings['context_gathering'] = context_duration
        logger.info(f"[TIMING] Context gathering completed in {context_duration:.3f} seconds")
        
        # Start timing AI service
        ai_start = datetime.now()
        
        # Get text response from selected AI service
        logger.info(f"[AI] Using {'OpenAI' if use_openai else 'Groq'} service...")
        
        # Use gathered results for AI call
        if use_openai:
            text_response = await app.state.openai_service.send_to_openai(
                transcript,
                vector_db_service=vector_results if vector_results is not None else None,
                chat_history_service=history,
                context_manager=context
            )
        else:
            text_response = await app.state.groq_service.send_to_groq(
                transcript,
                vector_db_service=vector_results if vector_results is not None else None,
                chat_history_service=history,
                context_manager=context
            )
        
        # Record timing for AI service
        ai_duration = (datetime.now() - ai_start).total_seconds()
        timings['ai_service'] = ai_duration
        logger.info(f"[TIMING] AI service completed in {ai_duration:.3f} seconds")
        
        logger.info(f"[AI] Received response ({len(text_response)} chars): {text_response[:30]}...")
        
        # Start timing TTS
        tts_start = datetime.now()
        
        # Process complete response in TTS
        audio_data = await tts_service.text_to_speech(text_response)
        
        # Record timing for TTS
        tts_duration = (datetime.now() - tts_start).total_seconds()
        timings['tts_service'] = tts_duration
        logger.info(f"[TIMING] TTS completed in {tts_duration:.3f} seconds")
        
        result = {
            "text": text_response,
            "audio": audio_data,
            "success": True
        }
        
        logger.info("[SUCCESS] Request processing completed")
        return result
        
    except Exception as e:
        logger.error(f"[ERROR] Request processing failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/generate")
async def generate(data: dict):
    try:
        request_start = datetime.now()
        
        # Track component timings
        timings = {
            'vector_db': 0,
            'ai_service': 0,
            'tts_service': 0
        }
        
        transcript = data.get('transcript', '')
        use_openai = data.get('use_openai', False)  # Get the flag from request
        
        logger.info(f"[AI] Using {'OpenAI' if use_openai else 'Groq'} service")

        result = await process_request(
            transcript, 
            app.state.groq_service, 
            app.state.tts_service,
            use_openai=use_openai,
            timings=timings
        )
        
        request_end = datetime.now()
        total_duration = (request_end - request_start).total_seconds()
        
        # Add timing info to response
        result['timing'] = {
            'total_duration': total_duration,
            **timings
        }
        
        return result
        
    except HTTPException as he:
        logger.error(f"[HTTP] HTTPException: {he.detail}")
        raise
    except Exception as e:
        logger.error(f"[HTTP] Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import platform
    import uvicorn
    
    logger.info("[STARTUP] Starting AI service...")
    
    config = {
        "host": "127.0.0.1",
        "port": 8013,
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