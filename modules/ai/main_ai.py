from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from typing import Dict
from dotenv import load_dotenv
from modules.ai.services.groq_service import GroqService
from modules.ai.services.tts_service import TTSService
from modules.ai.config.azure_config import get_groq_api_keys
from pathlib import Path
import uvicorn
import json

# Configure logging first, before any other operations
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/ai.log')
    ]
)

# Load environment variables
load_dotenv()

app = FastAPI()
logger = logging.getLogger(__name__)

# Create logs directory if it doesn't exist
Path("logs").mkdir(exist_ok=True)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    # Initialize services
    api_keys = get_groq_api_keys()
    groq_service = GroqService(api_keys)
    tts_service = TTSService()
    logger.info("Services initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize services: {e}", exc_info=True)
    raise

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket client connected")
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get('type') == 'generate':
                transcript = data.get('transcript', '')
                if not transcript:
                    await websocket.send_json({'success': False, 'error': 'No transcript provided'})
                    continue

                logger.info(f"AI service received transcript via WebSocket: {transcript}")
                
                try:
                    # Get text response from Groq
                    response = groq_service.send_to_groq(transcript)
                    logger.info(f"Got response from Groq: {response[:100]}...")
                    
                    # Generate audio from the response text using TTS service
                    logger.info("Attempting to generate audio...")
                    audio_data = await tts_service.text_to_speech(response)
                    
                    result = {
                        "text": response,
                        "audio": audio_data,
                        "success": True
                    }
                    await websocket.send_json(result)
                    
                except Exception as e:
                    logger.error(f"Error processing request: {e}")
                    await websocket.send_json({'success': False, 'error': str(e)})
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        logger.info("WebSocket client disconnected")

@app.post("/generate")
async def generate_response(data: Dict):
    try:
        transcript = data.get('transcript', '')
        if not transcript:
            raise HTTPException(status_code=400, detail="No transcript provided")
        
        logger.info(f"AI service received transcript: {transcript}")
        
        # Get text response from Groq
        response = groq_service.send_to_groq(transcript)
        logger.info(f"Got response from Groq: {response[:100]}...")
        
        # Generate audio from the response text using TTS service
        logger.info("Attempting to generate audio...")
        audio_data = await tts_service.text_to_speech(response)
        
        if audio_data:
            logger.info(f"Successfully generated audio, length: {len(audio_data)}")
        else:
            logger.warning("Failed to generate audio data")
        
        result = {
            "text": response,
            "audio": audio_data,
            "success": True
        }
        logger.info(f"Sending response with keys: {result.keys()}")
        return result
        
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Check if running on Windows
    import platform
    if platform.system() == "Windows":
        # Windows configuration (single worker)
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=8010,
            workers=1,  # Use single worker on Windows
            loop="asyncio",
            http="h11",
            ws="wsproto"
        )
    else:
        # Unix/Linux configuration (with multiple workers)
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=8010,
            workers=4,
            loop="uvloop",
            http="httptools",
            ws="websockets"
        ) 