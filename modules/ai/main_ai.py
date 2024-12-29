from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
from dotenv import load_dotenv
import logging

from modules.ai.services.ai_service import GroqService
from modules.ai.services.tts_service import TTSService
from src.config.azure_config import get_groq_api_keys
import uvicorn
import asyncio
from contextlib import asynccontextmanager
from colorama import init
from src.utils.logging_config import setup_logger

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
        app.state.api_keys = get_groq_api_keys()
        logger.info("[INIT] API keys loaded successfully")
        
        app.state.groq_service = GroqService(app.state.api_keys)
        logger.info("[INIT] Groq service initialized")
        
        app.state.tts_service = TTSService()
        logger.info("[INIT] TTS service initialized")
        
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

async def process_request(transcript: str, groq_service: GroqService, tts_service: TTSService) -> Dict:
    """Process a single request through the AI pipeline"""
    try:
        logger.info(f"[RECEIVE] Processing request: {transcript[:30]}...")
        
        # Get text response from Groq with all context services
        logger.info("[GROQ] Sending request to Groq API...")
        text_response = await groq_service.send_to_groq(
            transcript,
            vector_db_service=app.state.vector_service,  # You'll need to initialize this
            chat_history_service=app.state.history_service,  # You'll need to initialize this
            context_manager=app.state.context_manager  # You'll need to initialize this
        )
        logger.info(f"[GROQ] Received response ({len(text_response)} chars): {text_response[:30]}...")
        
        # Generate audio asynchronously
        logger.info("[TTS] Starting speech synthesis...")
        audio_task = asyncio.create_task(tts_service.text_to_speech(text_response))
        
        # Wait for audio generation
        audio_data = await audio_task
        audio_size = len(audio_data) if audio_data else 0
        logger.info(f"[TTS] Speech synthesis completed. Audio size: {audio_size} bytes")
        
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
        transcript = data.get('transcript', '')



        result = await process_request(transcript, app.state.groq_service, app.state.tts_service)
        
        # Add debug logging
        #logger.info(f"Audio data type: {type(result.get('audio'))}")
        #logger.info(f"Audio data length: {len(result['audio']) if result.get('audio') else 0}")
        #logger.info(f"Audio data starts with: {result['audio'][:50] if result.get('audio') else 'None'}")
        
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