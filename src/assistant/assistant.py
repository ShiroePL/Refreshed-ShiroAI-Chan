import logging
from typing import Dict, Optional
from src.config.azure_config import get_groq_api_keys
from src.services.ai_service import GroqService
from src.utils.error_handler import handle_error
from .tools import AssistantTool

logger = logging.getLogger(__name__)

class AIAgent:
    def __init__(self):
        try:
            # Initialize Groq service
            api_keys = get_groq_api_keys()
            self.groq_service = GroqService(api_keys)
            
            # Define the tool selection prompt
            self.tool_selection_prompt = """You are an AI assistant tasked with analyzing user input and determining the appropriate tool to handle it.

            Available tools:
            - CONVERSATION: For general questions, chat, information requests
            - ACTION: For requests requiring physical action or animation
            - SYSTEM: For system-related commands (shutdown, restart, etc)
            - WEB_SEARCH: For web search requests

            Based on the following input, context, and conversation history, return ONLY the name of the most appropriate tool (e.g., 'CONVERSATION', 'ACTION', or 'SYSTEM').

            User input: {input}
            Recent context: {context}
            Conversation history: {history}"""

            logger.info("Assistant initialized successfully")
        except Exception as e:
            handle_error(logger, e, "Assistant initialization")

    async def analyze_input(self, 
                          user_input: str, 
                          context: Optional[Dict] = None, 
                          history: Optional[list] = None) -> AssistantTool:
        """
        Analyze user input and determine which tool should handle it.
        Returns an AssistantTool enum value.
        """
        try:
            # Format the prompt with actual data
            prompt = self.tool_selection_prompt.format(
                input=user_input,
                context=context or "No context provided",
                history=history or "No history provided"
            )

            # Get tool decision from Groq
            response = await self.groq_service.send_to_groq(prompt)
            
            # Convert response to tool enum
            try:
                tool = AssistantTool[response.strip().upper()]
                logger.info(f"Selected tool: {tool.name} for input: {user_input}")
                return tool
            except KeyError:
                logger.warning(f"Invalid tool response: {response}, defaulting to CONVERSATION")
                return AssistantTool.CONVERSATION

        except Exception as e:
            logger.error(f"Error in input analysis: {e}")
            return AssistantTool.CONVERSATION  # Default to conversation on error 