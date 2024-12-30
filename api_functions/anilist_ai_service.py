from src.utils.logging_config import setup_logger
import httpx

# Setup module-specific logger
logger = setup_logger('anilist_ai')

class AnimeAIService:
    def __init__(self):
        self._groq_service = None
    
    @property
    def groq_service(self):
        if self._groq_service is None:
            # Instead of creating a new GroqService, make HTTP request to AI service
            from src.config.service_config import AI_SERVICE_URL
            logger.info("Using AI service for anime updates")
            self._groq_service = AI_SERVICE_URL
        return self._groq_service
    
    async def process_anime_update(self, user_question, database_messages):
        """Process anime update request through AI"""
        try:
            # Send request to AI service instead of direct Groq call
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.groq_service}/generate",
                    json={"transcript": database_messages}
                )
                if response.status_code == 200:
                    return response.json().get('text')
                return None
        except Exception as e:
            logger.error(f"Error processing anime update: {e}")
            return None 