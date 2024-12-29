from src.utils.logging_config import setup_logger

# Setup module-specific logger
logger = setup_logger('anilist_ai')

class AnimeAIService:
    def __init__(self):
        self._groq_service = None
    
    @property
    def groq_service(self):
        if self._groq_service is None:
            # Import here to avoid circular dependency
            from modules.ai.services.ai_service import GroqService
            from src.config.azure_config import get_groq_api_keys
            
            # Get API keys and pass them directly
            api_keys = get_groq_api_keys()
            logger.info("Initializing Groq service for anime updates")
            self._groq_service = GroqService(api_keys)
            
        return self._groq_service
    
    async def process_anime_update(self, user_question, database_messages):
        """Process anime update request through AI"""
        try:
            # send to groq for answer
            answer = await self.groq_service.send_to_groq(database_messages)
            return answer
        except Exception as e:
            logger.error(f"Error processing anime update: {e}")
            return None 