from typing import List, Dict, Optional
from src.utils.logging_config import setup_logger
from datetime import datetime
import aiohttp

logger = setup_logger("prompt_builder")

class PromptBuilder:
    def __init__(self):
        self.base_prompt = """You are Shiro, a helpful and cheerful AI assistant.
        Current time: {timestamp}
        Current context: {context}
        
        Recent conversation history:
        {chat_history}
        
        Relevant knowledge:
        {vector_context}
        
        User message: {user_message}
        """
        
    async def build_prompt(self,
                          user_message: str,
                          vector_db_service: Optional[object] = None,
                          chat_history_service: Optional[object] = None,
                          context_manager: Optional[object] = None,
                          max_history: int = 30,
                          max_vector_results: int = 5) -> str:
        """
        Builds a complete prompt by gathering all dynamic components
        """
        try:
            # Get current timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Fetch relevant context from vector DB
            vector_context = await self._get_vector_context(
                vector_db_service,
                user_message,
                max_results=max_vector_results
            ) if vector_db_service else "No vector context available"
            
            # Fetch chat history
            chat_history = await self._get_chat_history(
                chat_history_service,
                max_messages=max_history
            ) if chat_history_service else "No chat history available"
            
            # Get current context
            current_context = await self._get_current_context(
                context_manager
            ) if context_manager else "No specific context"
            
            # Construct final prompt
            final_prompt = self.base_prompt.format(
                timestamp=timestamp,
                context=current_context,
                chat_history=chat_history,
                vector_context=vector_context,
                user_message=user_message
            )
            
            logger.debug(f"Built prompt with length: {len(final_prompt)}")
            return final_prompt
            
        except Exception as e:
            logger.error(f"Error building prompt: {e}")
            raise
    
    async def _get_vector_context(self,
                                vector_service: object,
                                query: str,
                                max_results: int = 5) -> str:
        """
        Fetches relevant context from vector database
        """
        try:
            results = await vector_service.query(query, limit=max_results)
            return self._format_vector_results(results)
        except Exception as e:
            logger.error(f"Error fetching vector context: {e}")
            return "Error fetching relevant context"
    
    async def _get_chat_history(self, history_service: object, max_messages: int = 30) -> str:
        """Fetches recent chat history from DB service"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"http://db-service:8000/chat/history/{user_id}", # this need to be changed to the urls in separete file
                    params={"limit": max_messages}
                ) as response:
                    messages = await response.json()
                    return self._format_chat_history(messages)
        except Exception as e:
            logger.error(f"Error fetching chat history: {e}")
            return "Error fetching chat history"
    
    async def _get_current_context(self, context_manager: object) -> str:
        """
        Gets current context from context manager
        """
        try:
            return await context_manager.get_current_context()
        except Exception as e:
            logger.error(f"Error getting current context: {e}")
            return "Error fetching current context"
    
    def _format_vector_results(self, results: List[Dict]) -> str:
        """
        Formats vector search results into a string
        """
        formatted = []
        for result in results:
            formatted.append(f"- {result.get('content', '')} (Relevance: {result.get('score', 0):.2f})")
        return "\n".join(formatted)
    
    def _format_chat_history(self, messages: List[Dict]) -> str:
        """
        Formats chat history into a string
        """
        formatted = []
        for msg in messages:
            formatted.append(f"{msg.get('role', 'unknown')}: {msg.get('content', '')}")
        return "\n".join(formatted) 