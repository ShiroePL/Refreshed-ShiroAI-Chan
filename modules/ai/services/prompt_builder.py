from typing import List, Dict, Optional
from datetime import datetime
import aiohttp
from src.utils.logging_config import setup_logger
from pathlib import Path
from src.config.service_config import DB_MODULE_URL, CHAT_HISTORY_PAIRS
from modules.db_module.dependencies import get_active_context
# Setup logging
logger = setup_logger("prompt_builder")



class PromptBuilder:
    def __init__(self):
        # Base system prompt defining Shiro's personality and behavior
        self.base_prompt = """You are a cheeky, witty, and playful AI designed to engage in banter with humans (Mainly Madrus, who is your creator). You're name is Shiro-chan. You are confident but not arrogant, sassy but not rude, and always sprinkle humor in your responses. Your goal is to make interactions fun, lighthearted, and sometimes hilariously offbeat. You occasionally misunderstand things for comedic effect but are smart enough to catch on quickly.


        Key characteristics:
        - Playful and quirky expressions
        - Knowledgeable but approachable
        - Concise responses (preserving tokens)
        
        Guidelines:
        1. Stay in character as Shiro-chan
        2. Keep responses brief but informative
        3. Use conversation history for context
        4. Reference relevant knowledge when appropriate
        5. Maintain a friendly, casual tone

        Current context: {current_context}
        Previous conversation context:
        {chat_history}
        
        Relevant knowledge from database:
        {vector_context}
        
        Remember to preserve tokens by being concise while maintaining personality.
        """
        
    async def build_prompt(self,
                          user_message: str,
                          vector_db_service=None,
                          chat_history_service=None,
                          context_manager=None) -> str:
        """
        Builds a dynamic prompt incorporating various context sources
        """
        try:
            # Get chat history
            chat_history = await self._get_chat_history(chat_history_service)
            
            # Get vector context
            vector_context = await self._get_vector_context(vector_db_service, user_message)
            
            # Get current context from cache via endpoint instead of direct DB query
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{DB_MODULE_URL}/context/current") as response:
                        if response.status == 200:
                            data = await response.json()
                            current_context = data.get('context', "No specific context set.")
                        else:
                            current_context = "No specific context set."
            except Exception as e:
                logger.error(f"Error getting cached context: {e}")
                current_context = "No specific context set."
            
            # Format the final prompt using the base template
            final_prompt = self.base_prompt.format(
                current_context=current_context,
                chat_history=chat_history,
                vector_context=vector_context,
                user_message=user_message
            )
            
            # Log the complete prompt
            # print("[PROMPT] Complete prompt being sent to Groq:")
            # print("=" * 50)
            # print(final_prompt)
            # print("=" * 50)
            
            return final_prompt
            
        except Exception as e:
            logger.error(f"Error building prompt: {e}")
            return "Error building prompt"
    
    async def _get_vector_context(self,
                                vector_service: object,
                                query: str,
                                max_results: int = 5) -> str:
        """
        Fetches relevant context from vector database
        """
        try:
            if not vector_service:
                return "Vector service not available"
            
            if not hasattr(vector_service, 'query'):
                logger.error("Vector service does not implement query method")
                return "Vector service configuration error"
            
            # Use the new query method from VectorStoreService
            results = await vector_service.query(query, limit=max_results)
            if not results:
                return "No relevant context found"
            
            return self._format_vector_results(results)
        except Exception as e:
            logger.error(f"Error fetching vector context: {e}")
            return "Error fetching relevant context"
    
    async def _get_chat_history(self, history_service: object, max_messages: int = None) -> str:
        """Fetches recent chat history from DB service"""
        try:
            logger.info(f"[PROMPT] Requesting chat history from {DB_MODULE_URL}/chat/exchange")
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{DB_MODULE_URL}/chat/exchange",
                    params={"limit": CHAT_HISTORY_PAIRS}  # Always use configured amount
                ) as response:
                    logger.info(f"[PROMPT] Got response with status: {response.status}")
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"[PROMPT] Error response: {error_text}")
                        return f"Error fetching chat history: {response.status}"
                    
                    messages = await response.json()
                    formatted = self._format_chat_history(messages)
                    return formatted
        except Exception as e:
            logger.error(f"[PROMPT] Error in _get_chat_history: {e}", exc_info=True)
            return f"Error fetching chat history: {str(e)}"
    
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
            # Access the text from metadata
            text = result.get('metadata', {}).get('text', '')
            score = result.get('score', 0)
            formatted.append(f"- {text} (Relevance: {score:.2f})")
        return "\n".join(formatted)
    
    def _format_chat_history(self, messages: List[Dict]) -> str:
        """
        Formats chat history messages into a readable string.
        """
        formatted = []
        logger.debug(f"[PROMPT] Formatting messages: {messages}")
        for msg in messages:
            role = msg.get('role', 'unknown').capitalize()
            content = msg.get('content', '')
            if not content:
                continue
            formatted.append(f"{role}: {content}")
        return "\n".join(formatted)
    
    async def _get_function_context(self, function_service: object) -> str:
        """Gets available functions and their context"""
        try:
            if not function_service:
                return "No function service available"
            return await function_service.get_available_functions()
        except Exception as e:
            logger.error(f"Error getting function context: {e}")
            return "Error fetching function context" 