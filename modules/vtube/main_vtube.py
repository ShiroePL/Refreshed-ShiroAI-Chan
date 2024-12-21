from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
from services.vtube.vtube_studio_api import VTubeStudioAPI  # Updated import

app = FastAPI()
logger = logging.getLogger(__name__)

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
    filename='logs/vtube.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class AnimationController:
    def __init__(self):
        self.vtube_api = None
        self.connect_to_vtube()

    def connect_to_vtube(self):
        try:
            self.vtube_api = VTubeStudioAPI()
            logger.info("VTube Studio API connected successfully")
        except Exception as e:
            logger.error(f"Failed to connect to VTube Studio: {e}")
            raise

    async def analyze_and_play_animation(self, text: str, mood: str = None):
        try:
            if not self.vtube_api or not self.vtube_api.connected:
                raise HTTPException(status_code=503, detail="VTube Studio not connected")

            if mood:
                animation = mood
            elif "happy" in text.lower():
                animation = "happy"
            elif "sad" in text.lower():
                animation = "sad"
            else:
                animation = "introduce"

            logger.info(f"Playing animation: {animation}")
            self.vtube_api.play_animation(animation)
            return {"success": True, "animation": animation}

        except Exception as e:
            logger.error(f"Error playing animation: {e}")
            raise HTTPException(status_code=500, detail=str(e))

controller = AnimationController()

@app.post("/animate")
async def animate(data: dict):
    text = data.get('transcript', '')
    mood = data.get('mood')
    return await controller.analyze_and_play_animation(text, mood) 