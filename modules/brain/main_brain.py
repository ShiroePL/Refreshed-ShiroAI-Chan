from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import httpx
import logging
from typing import Dict
from pydantic import BaseModel, ValidationError
import os
from pathlib import Path
from colorama import init, Fore, Style
import time
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
            
            logger.info(f"Brain received from AI: {response_data.keys()}")
            if 'audio' in response_data:
                audio_length = len(response_data['audio']) if response_data['audio'] else 0
                logger.info(f"Audio data present, length: {audio_length}")
            else:
                logger.warning("No audio data in AI response")
            
            return response_data
            
    except httpx.RequestError as e:
        logger.error(f"AI service request failed: {e}")
        raise HTTPException(status_code=502, detail=f"AI service request failed: {e}")

async def call_vtube_service(data: Dict, animation_name: str) -> Dict:
    """Forward request to VTube animation server with detailed logging."""
    try:
        animation_data = {
            "text": data["transcript"],
            "mood": animation_name  # Animation server expects 'mood' parameter
        }
        
        async with httpx.AsyncClient() as client:
            logger.info(f"Sending animation request: {animation_data}")
            response = await client.post(f"{VTUBE_SERVICE_URL}/play_animation", json=animation_data)
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as e:
        logger.error(f"Animation server request failed: {e}")
        raise HTTPException(status_code=502, detail=f"Animation server request failed: {e}")
    except httpx.HTTPStatusError as e:
        logger.error(f"Animation server returned error: {e.response.status_code}, {e.response.text}")
        raise HTTPException(status_code=502, detail=f"Animation server error: {e.response.status_code}, {e.response.text}")


@app.post("/process")
async def process_input(request: Request):
    try:
        data = await request.json()
        logger.info(f"Received data: {data}")
        
        # Validate the input
        try:
            input_data = InputData(**data)
        except ValidationError as ve:
            logger.error(f"Validation error: {ve}")
            raise HTTPException(status_code=400, detail="Invalid input data")
        
        # Analyze input type
        input_type, animation_name = await analyze_input(input_data.transcript)
        
        # Route to appropriate service
        if input_type == "animation":
            # Call VTube service with specific animation
            vtube_response = await call_vtube_service(data, animation_name)
            # Also get AI response for animation requests
            ai_response = await call_ai_service(data)
            # Combine responses
            response = {**vtube_response, **ai_response}
            logger.info(f"Combined response structure: {response.keys()}")
        else:  # conversation
            response = await call_ai_service(data)
            logger.info(f"AI service response structure: {response.keys()}")
        
        # Validate response has required fields
        if 'text' not in response:
            logger.error("Response missing required 'text' field")
            raise HTTPException(status_code=502, detail="Invalid service response")
            
        # Log final response structure
        logger.info(f"Final response keys: {response.keys()}")
        if 'audio' in response:
            logger.info("Audio data present in final response")
            
        return response
        
    except httpx.RequestError as e:
        logger.error(f"HTTP request error: {e}")
        raise HTTPException(status_code=502, detail="Service request failed")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Run the application
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting FastAPI application with Doppler configuration")
    uvicorn.run(app, host="shiropc", port=8015)
