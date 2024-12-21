from enum import Enum

class AssistantState(Enum):
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    LISTENING_COMMAND = "LISTENING_COMMAND"
    PROCESSING = "PROCESSING"
    SPEAKING = "SPEAKING"
    ERROR = "ERROR" 