from enum import Enum, auto

class AssistantTool(Enum):
    """Enum representing different tools/actions the assistant can choose from"""
    CONVERSATION = auto()  # Regular conversation/response
    ACTION = auto()        # Physical action/animation
    SYSTEM = auto()        # System commands (shutdown, restart etc)
    WEB_SEARCH = auto()   # Web search
    # Add more tools as needed 