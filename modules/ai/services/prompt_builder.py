from typing import List, Dict, Optional
from datetime import datetime
import aiohttp
from src.utils.logging_config import setup_logger
from pathlib import Path
from src.config.service_config import DB_MODULE_URL
# Setup logging
logger = setup_logger("prompt_builder")

# Create logs directory if it doesn't exist
Path("logs").mkdir(exist_ok=True)

# Add handlers if none exist
if not logger.handlers:
    # File handler
    file_handler = logger.FileHandler('logs/prompt_builder.log')
    file_handler.setFormatter(logger.Formatter(
        '%(asctime)s - [%(name)s] - %(levelname)s - %(message)s'
    ))
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logger.StreamHandler()
    console_handler.setFormatter(logger.Formatter(
        '%(asctime)s - [%(name)s] - %(levelname)s - %(message)s'
    ))
    logger.addHandler(console_handler)

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
            
            # Get current context
            #current_context = await self._get_current_context(context_manager)
            current_context = "Currently you are speaking with Madrus and he is testing new functions and cooking some code so it is a lot of the same stupid questions."
            # Build the final prompt
            final_prompt = (
                "You are Shiro-chan, a friendly  AI assistant with a cat-like personality. Madrus is creating you to be his best girl friend and be like AI person to talk to."
                "You often use funny and quirky expressions. You're knowledgeable but playful.\n\n"
                f"Previous conversation context:\n{chat_history}\n\n"
                f"Relevant knowledge context:\n{vector_context}\n\n"
                f"Current context:\n{current_context}\n\n"
                "Remember to stay in character as Shiro-chan while remembering the conversation history and the relevant knowledge contexts."
                "Also dont answer with too much text, just answer the question and if you need to explain something, do it in a few sentences. We need to preserve tokens for testing as we burning a lot if tokens for this testing."
            )
            
            # Log the complete prompt
            logger.info("[PROMPT] Complete prompt being sent to Groq:")
            logger.info("=" * 50)
            logger.info(final_prompt)
            logger.info("=" * 50)
            
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
    
    async def _get_chat_history(self, history_service: object, max_messages: int = 30) -> str:
        """Fetches recent chat history from DB service"""
        try:
            logger.info(f"[PROMPT] Requesting chat history from {DB_MODULE_URL}/chat/exchange")
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{DB_MODULE_URL}/chat/exchange",
                    params={"limit": max_messages}
                ) as response:
                    logger.info(f"[PROMPT] Got response with status: {response.status}")
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"[PROMPT] Error response: {error_text}")
                        return f"Error fetching chat history: {response.status}"
                    
                    messages = await response.json()
                    # Add detailed logging of received messages
                    for msg in messages:
                        logger.info(
                            f"[PROMPT] Message - Question: {msg.get('question', '')[:30]}... "
                            f"Answer: {msg.get('answer', '')[:30]}..."
                        )
                    formatted = self._format_chat_history(messages)
                    logger.info(f"[PROMPT] Formatted history preview: {formatted[:200]}...")
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
        for msg in messages:
            role = msg.get('role', 'unknown').capitalize()
            content = msg.get('content', '')
            formatted.append(f"{role}: {content}")
        return "\n".join(formatted) 