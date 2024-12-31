from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import httpx
from typing import Dict, Optional
from pydantic import BaseModel
import os
from colorama import init
import asyncio
from src.utils.logging_config import setup_logger
from asyncio import Queue, create_task
from collections import defaultdict
import uuid
import aiohttp
# Initialize colorama for Windows compatibility
init()
# Setup module-specific logger
logger = setup_logger('brain')

# Create custom logger formatter with colors

# Initialize the FastAPI app
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5000", "http://localhost:5000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Fetch service URLs from Doppler configuration or fallback to defaults
AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://127.0.0.1:8013")
VTUBE_SERVICE_URL = os.getenv("VTUBE_SERVICE_URL", "http://localhost:5001")
DB_MODULE_URL = os.getenv("DB_MODULE_URL", "http://127.0.0.1:8013")

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
            response = await client.post(f"{AI_SERVICE_URL}/generate", json=data, timeout=15.0)
            response.raise_for_status()
            return response.json()
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

class ResponseQueue:
    def __init__(self):
        self.pending_responses: Dict[str, Queue] = defaultdict(Queue)
        self.current_conversation: Optional[str] = None
    
    async def queue_response(self, conversation_id: str, response: dict):
        await self.pending_responses[conversation_id].put(response)
    
    async def get_next_response(self, conversation_id: str) -> dict:
        return await self.pending_responses[conversation_id].get()

    def set_current_conversation(self, conversation_id: str):
        self.current_conversation = conversation_id

class BrainService:
    def __init__(self):
        self.response_queue = ResponseQueue()
    
    async def process_long_running_task(self, data: dict, conversation_id: str):
        try:
            # Use the global call_ai_service function
            result = await call_ai_service(data)
            # Queue the response
            await self.response_queue.queue_response(conversation_id, result)
        except Exception as e:
            logger.error(f"Error in long-running task: {e}")
            # Queue error response
            error_response = {
                "success": False,
                "error": str(e),
                "text": "I apologize, but I encountered an error processing your request."
            }
            await self.response_queue.queue_response(conversation_id, error_response)

    async def process_input(self, request: Request):
        data = await request.json()
        conversation_id = data.get('conversation_id', str(uuid.uuid4()))
        
        # Set this as the current conversation
        self.response_queue.set_current_conversation(conversation_id)
        
        # Start long-running task without waiting
        create_task(self.process_long_running_task(data, conversation_id))
        
        # Return immediately
        return {
            "status": "processing",
            "conversation_id": conversation_id
        }

    async def get_pending_response(self, conversation_id: str):
        try:
            # Get response when ready
            if self.response_queue.current_conversation == conversation_id:
                response = await self.response_queue.get_next_response(conversation_id)
                return response
            return {"status": "waiting"}
        except Exception as e:
            logger.error(f"Error getting pending response: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

# Initialize BrainService
brain_service = BrainService()

@app.post("/process")
async def process_input(request: Request):
    return await brain_service.process_input(request)

@app.get("/pending_response/{conversation_id}")
async def get_pending_response(conversation_id: str):
    return await brain_service.get_pending_response(conversation_id)

@app.post("/context/update")
async def update_context(context_text: str):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{DB_MODULE_URL}/context/update",
                json={"context_text": context_text}
            ) as response:
                if response.status != 200:
                    raise HTTPException(status_code=response.status, detail="Failed to update context")
                return await response.json()
    except Exception as e:
        logger.error(f"Error updating context: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting FastAPI application with Doppler configuration")
    uvicorn.run(app, host="127.0.0.1", port=8015)
