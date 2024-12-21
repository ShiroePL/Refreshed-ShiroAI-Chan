from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from typing import Dict, Optional
from dotenv import load_dotenv
from modules.ai.services.groq_service import GroqService
from modules.ai.services.tts_service import TTSService
from modules.ai.config.azure_config import get_groq_api_keys
from pathlib import Path
import uvicorn
import json
import asyncio
from contextlib import asynccontextmanager

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/ai.log')
    ]
)

logger = logging.getLogger(__name__)

# Create logs directory
Path("logs").mkdir(exist_ok=True)

# Load environment variables
load_dotenv()

# Initialize services at startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize services on startup
    try:
        app.state.api_keys = get_groq_api_keys()
        app.state.groq_service = GroqService(app.state.api_keys)
        app.state.tts_service = TTSService()
        logger.info("Services initialized successfully")
        yield
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}", exc_info=True)
        raise
    finally:
        # Cleanup on shutdown
        logger.info("Shutting down AI service")

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
        # Get text response from Groq
        response = groq_service.send_to_groq(transcript)
        logger.info(f"Got response from Groq: {response[:100]}...")
        
        # Generate audio from the response text
        logger.info("Generating audio response...")
        audio_data = await tts_service.text_to_speech(response)
        
        return {
            "text": response,
            "audio": audio_data,
            "success": True
        }
    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket client connected")
    
    try:
        while True:
            try:
                data = await websocket.receive_json()
                
                if data.get('type') == 'generate':
                    transcript = data.get('transcript', '')
                    if not transcript:
                        await websocket.send_json({
                            'success': False, 
                            'error': 'No transcript provided'
                        })
                        continue

                    logger.info(f"Processing transcript: {transcript}")
                    
                    # Process request through AI pipeline
                    result = await process_request(
                        transcript, 
                        app.state.groq_service, 
                        app.state.tts_service
                    )
                    
                    await websocket.send_json(result)
                    
            except WebSocketDisconnect:
                logger.info("WebSocket client disconnected")
                break
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                await websocket.send_json({
                    'success': False,
                    'error': str(e)
                })
                
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        logger.info("WebSocket connection closed")

@app.post("/generate")
async def generate_response(data: Dict):
    """HTTP endpoint for generating responses"""
    try:
        transcript = data.get('transcript')
        if not transcript:
            raise HTTPException(status_code=400, detail="No transcript provided")
        
        logger.info(f"Processing HTTP request with transcript: {transcript}")
        
        result = await process_request(
            transcript,
            app.state.groq_service,
            app.state.tts_service
        )
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result['error'])
            
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing HTTP request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import platform
    config = {
        "host": "0.0.0.0",
        "port": 8010,
        "loop": "asyncio",
        "ws_ping_interval": 20,  # Keep WebSocket connections alive
        "ws_ping_timeout": 20,
    }
    
    if platform.system() == "Windows":
        config.update({
            "workers": 1,
            "http": "h11",
            "ws": "wsproto"
        })
    else:
        config.update({
            "workers": 4,
            "loop": "uvloop",
            "http": "httptools",
            "ws": "websockets"
        })
        
    uvicorn.run(app, **config)