from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import httpx
import logging
from typing import Dict
from pydantic import BaseModel, ValidationError
import os

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

# Configure logging
logging.basicConfig(
    filename='logs/brain.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Fetch service URLs from Doppler configuration or fallback to defaults
AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:8010")
VTUBE_SERVICE_URL = os.getenv("VTUBE_SERVICE_URL", "http://localhost:8002")

# Define the request model
class InputData(BaseModel):
    transcript: str

class ResponseData(BaseModel):
    text: str
    audio: str | None = None  # Add audio field to response model

async def analyze_input(text: str) -> str:
    """Determine the type of input and required processing"""
    animation_keywords = ['animate', 'expression', 'mood', 'happy', 'sad', 'angry']
    text_lower = text.lower()
    for keyword in animation_keywords:
        if keyword in text_lower:
            return "animation"
    return "conversation"

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

async def call_vtube_service(data: Dict) -> Dict:
    """Forward request to VTube service with detailed logging."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{VTUBE_SERVICE_URL}/animate", json=data)
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as e:
        logger.error(f"VTube service request failed: {e}")
        raise HTTPException(status_code=502, detail=f"VTube service request failed: {e}")
    except httpx.HTTPStatusError as e:
        logger.error(f"VTube service returned error: {e.response.status_code}, {e.response.text}")
        raise HTTPException(status_code=502, detail=f"VTube service error: {e.response.status_code}, {e.response.text}")


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
        input_type = await analyze_input(input_data.transcript)
        
        # Route to appropriate service
        if input_type == "conversation":
            response = await call_ai_service(data)
            # Log the response structure
            logger.info(f"AI service response structure: {response.keys()}")
        elif input_type == "animation":
            response = await call_vtube_service(data)
            # Also get AI response for animation requests
            ai_response = await call_ai_service(data)
            # Ensure audio data is preserved when merging responses
            response.update(ai_response)
            logger.info(f"Combined response structure: {response.keys()}")
        
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
    uvicorn.run(app, host="0.0.0.0", port=8015)
