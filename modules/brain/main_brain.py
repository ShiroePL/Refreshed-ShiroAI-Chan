from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import httpx
import logging
import time  # Add this import
from typing import Dict
from pydantic import BaseModel, ValidationError
import os
from pathlib import Path
from colorama import init, Fore, Style
import asyncio
# Initialize colorama for Windows compatibility
init()

# Create custom logger formatter with colors
class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors"""
    
    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Style.BRIGHT,
        
        # Custom labels
        'CONNECT': Fore.BLUE + Style.BRIGHT,
        'DISCONNECT': Fore.MAGENTA,
        'STATUS': Fore.CYAN,
        'RECEIVE': Fore.GREEN,
        'PROCESS': Fore.YELLOW,
        'ANALYSIS': Fore.BLUE,
        'ROUTE': Fore.MAGENTA,
        'AI': Fore.CYAN + Style.BRIGHT,
        'SEND': Fore.GREEN + Style.BRIGHT,
        'SUCCESS': Fore.GREEN + Style.BRIGHT,
        'WARNING': Fore.YELLOW + Style.BRIGHT,
        'ERROR': Fore.RED + Style.BRIGHT,
        'COMBINE': Fore.CYAN,
    }

    def format(self, record):
        # Color the log level
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{Style.RESET_ALL}"
        
        # Color the custom labels in the message [LABEL]
        for label, color in self.COLORS.items():
            if f"[{label}]" in record.msg:
                record.msg = record.msg.replace(
                    f"[{label}]",
                    f"{color}[{label}]{Style.RESET_ALL}"
                )
        
        return super().format(record)

# Create logs directory if it doesn't exist
Path("logs").mkdir(exist_ok=True)

# Configure logging with colored formatter
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Console handler with colors
console_handler = logging.StreamHandler()
console_handler.setFormatter(ColoredFormatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))

# File handler without colors (plain text)
file_handler = logging.FileHandler('logs/brain.log')
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))

# Add both handlers
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Silence uvicorn access logs
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("uvicorn.error").setLevel(logging.WARNING)

# Initialize the FastAPI app
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Fetch service URLs from Doppler configuration or fallback to defaults
AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://shiropc:8013")
VTUBE_SERVICE_URL = os.getenv("VTUBE_SERVICE_URL", "http://localhost:5001")

# Define the request model
class InputData(BaseModel):
    transcript: str

class ResponseData(BaseModel):
    text: str
    audio: str | None = None  # Add audio field to response model

async def analyze_input(text: str) -> str:
    """Determine the type of input and required processing"""
    animation_keywords = {
        'introduction': ['hello', 'hi', 'hey', 'greetings'],
        # Add more animations and their trigger keywords here
    }
    
    text_lower = text.lower()
    
    # Check for animation triggers
    for animation, keywords in animation_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            return "animation", animation
            
    return "conversation", None

async def call_ai_service(data: Dict) -> Dict:
    """Forward request to AI service with detailed logging."""
    try:
        async with httpx.AsyncClient() as client:
            logger.info(f"Brain sending to AI service: {data}")
            response = await client.post(f"{AI_SERVICE_URL}/generate", json=data, timeout=30.0)
            response.raise_for_status()
            response_data = response.json()
            
            # Add debug logging
            if 'audio' in response_data:
                audio = response_data['audio']
    
            
            return response_data
            
    except httpx.RequestError as e:
        logger.error(f"AI service request failed: {e}")
        raise HTTPException(status_code=502, detail=f"AI service request failed: {e}")

async def call_vtube_service(animation_data: Dict) -> Dict:
    """Asynchronously call VTube service for animation analysis"""
    try:
        async with httpx.AsyncClient() as client:
            # Create a copy for logging only
            log_data = {
                'text': animation_data['text'],
                'ai_response': {
                    'text': animation_data['ai_response']['text'],
                    'audio': '<audio_data>' if 'audio' in animation_data['ai_response'] else None
                },
                'context': animation_data['context']
            }
            logger.info(f"Sending animation request: {log_data}")
            
            response = await client.post(
                f"{VTUBE_SERVICE_URL}/play_animation",
                json=animation_data,
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Animation analysis failed: {e}")
        return {"success": False, "error": str(e)}

@app.post("/process")
async def process_input(request: Request):
    try:
        data = await request.json()
        logger.info(f"Received data: {data}")
        
        # Create tasks for parallel processing
        ai_task = asyncio.create_task(call_ai_service(data))
        
        # Wait for AI response first since we need it for animation
        ai_response = await ai_task
        
        # Now create animation analysis task
        animation_data = {
            "text": data["transcript"],
            "ai_response": ai_response,
            "context": {
                "recent_mood": data.get("recent_mood"),
                "conversation_context": data.get("context"),
                "user_state": data.get("user_state")
            }
        }
        
        # Create animation task
        animation_task = asyncio.create_task(call_vtube_service(animation_data))
        
        # Wait for all tasks to complete
        animation_result = await animation_task
        
        # Combine results
        response = {
            **ai_response,
            'animation_data': animation_result
        }
        
        logger.info("All tasks completed successfully")
        return response
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Run the application
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting FastAPI application with Doppler configuration")
    uvicorn.run(app, host="shiropc", port=8015)
