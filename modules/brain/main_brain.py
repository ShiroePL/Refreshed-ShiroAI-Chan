from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import httpx
import logging
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
AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:8013")
VTUBE_SERVICE_URL = os.getenv("VTUBE_SERVICE_URL", "http://localhost:8002")

# Define the request model
class InputData(BaseModel):
    transcript: str

class ResponseData(BaseModel):
    text: str
    audio: str | None = None  # Add audio field to response model

async def analyze_input(text: str) -> str:
    # """Determine the type of input and required processing"""
    # animation_keywords = ['animate', 'expression', 'mood', 'happy', 'sad', 'angry']
    # text_lower = text.lower()
    # for keyword in animation_keywords:
    #     if keyword in text_lower:
    #         return "animation"
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

class WebSocketManager:
    def __init__(self):
        self.active_connections = set()
        self.ping_interval = 20  # seconds
        self._background_tasks = set()
        self.reconnect_attempts = {}  # Track reconnection attempts per client
        self.max_reconnect_attempts = 5
        self.reconnect_interval = 2  # seconds

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        client_id = id(websocket)
        logger.info(f"[CONNECT] New WebSocket client connected [ID: {client_id}]")
        logger.info(f"[STATUS] Total active connections: {len(self.active_connections)}")
        
        # Start ping task for this connection
        task = asyncio.create_task(self.ping_client(websocket, client_id))
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

    def disconnect(self, websocket: WebSocket):
        client_id = id(websocket)
        self.active_connections.discard(websocket)
        logger.info(f"[DISCONNECT] WebSocket client disconnected [ID: {client_id}]")
        logger.info(f"[STATUS] Total active connections: {len(self.active_connections)}")
        
        # Start reconnection attempt if not already trying
        if client_id not in self.reconnect_attempts:
            task = asyncio.create_task(self.attempt_reconnect(websocket, client_id))
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)

    async def attempt_reconnect(self, websocket: WebSocket, client_id: int):
        """Attempt to reconnect to a disconnected client"""
        self.reconnect_attempts[client_id] = 0
        
        while self.reconnect_attempts[client_id] < self.max_reconnect_attempts:
            try:
                logger.info(f"[RECONNECT] Attempting to reconnect to client [{client_id}] (attempt {self.reconnect_attempts[client_id] + 1})")
                
                # Try to reestablish connection
                await websocket.accept()
                self.active_connections.add(websocket)
                logger.info(f"[SUCCESS] Reconnected to client [{client_id}]")
                
                # Restart ping task
                task = asyncio.create_task(self.ping_client(websocket, client_id))
                self._background_tasks.add(task)
                task.add_done_callback(self._background_tasks.discard)
                
                # Clear reconnection attempts
                del self.reconnect_attempts[client_id]
                return
                
            except Exception as e:
                self.reconnect_attempts[client_id] += 1
                if self.reconnect_attempts[client_id] >= self.max_reconnect_attempts:
                    logger.error(f"[ERROR] Failed to reconnect to client [{client_id}] after {self.max_reconnect_attempts} attempts")
                    del self.reconnect_attempts[client_id]
                    return
                    
                logger.warning(f"[RETRY] Reconnection attempt {self.reconnect_attempts[client_id]} failed: {e}")
                await asyncio.sleep(self.reconnect_interval)

    async def ping_client(self, websocket: WebSocket, client_id: int):
        """Keep connection alive with periodic pings"""
        try:
            while True:
                await asyncio.sleep(self.ping_interval)
                try:
                    await websocket.send_json({"type": "ping"})
                except Exception as e:
                    logger.warning(f"[PING] Failed to ping client [{client_id}]: {e}")
                    if client_id not in self.reconnect_attempts:
                        self.disconnect(websocket)
                    break
        except Exception as e:
            logger.error(f"[ERROR] Ping task error for client [{client_id}]: {e}")
            if client_id not in self.reconnect_attempts:
                self.disconnect(websocket)

# Create WebSocket manager instance
ws_manager = WebSocketManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    client_id = id(websocket)
    
    try:
        while True:
            try:
                # Add timeout to receive_json
                data = await asyncio.wait_for(websocket.receive_json(), timeout=60.0)
                
                # Handle ping messages
                if data.get('type') == 'ping':
                    await websocket.send_json({"type": "pong"})
                    continue
                
                logger.info(f"[RECEIVE] Message from client [{client_id}]: {data.get('type', 'unknown_type')}")
                
                if data.get('type') == 'process':
                    transcript = data.get('transcript', '')
                    if not transcript:
                        logger.warning(f"[WARNING] Empty transcript from client [{client_id}]")
                        await websocket.send_json({
                            'success': False, 
                            'error': 'No transcript provided'
                        })
                        continue

                    logger.info(f"[PROCESS] Processing transcript: {transcript[:100]}...")
                    
                    # Analyze input type
                    input_type = await analyze_input(transcript)
                    logger.info(f"[ANALYSIS] Determined input type: {input_type}")
                    
                    # Route to appropriate service(s)
                    if input_type == "conversation":
                        logger.info("[ROUTE] Routing to AI service...")
                        response = await call_ai_service({"transcript": transcript})
                        logger.info("[AI] Received response from AI service")
                    elif input_type == "animation":
                        logger.info("[ROUTE] Routing to VTube service...")
                        response = await call_vtube_service({"transcript": transcript})
                        logger.info("[ROUTE] Also routing to AI service...")
                        ai_response = await call_ai_service({"transcript": transcript})
                        response.update(ai_response)
                        logger.info("[COMBINE] Combined responses from services")
                    
                    logger.info(f"[SEND] Sending response back to client [{client_id}]")
                    await websocket.send_json(response)
                    logger.info("[SUCCESS] Response sent successfully")
                    
            except asyncio.TimeoutError:
                # Send ping to check if connection is still alive
                try:
                    await websocket.send_json({"type": "ping"})
                except WebSocketDisconnect:
                    logger.info(f"[DISCONNECT] Client timed out and disconnected")
                    ws_manager.disconnect(websocket)
                    break
            except WebSocketDisconnect:
                ws_manager.disconnect(websocket)
                break
            except Exception as e:
                logger.error(f"[ERROR] Error processing message: {str(e)}", exc_info=True)
                try:
                    await websocket.send_json({
                        'success': False,
                        'error': str(e)
                    })
                except WebSocketDisconnect:
                    ws_manager.disconnect(websocket)
                    break
                
    except Exception as e:
        logger.error(f"[ERROR] WebSocket error: {str(e)}", exc_info=True)
        ws_manager.disconnect(websocket)

# Run the application
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting FastAPI application with Doppler configuration")
    uvicorn.run(app, host="0.0.0.0", port=8015)
