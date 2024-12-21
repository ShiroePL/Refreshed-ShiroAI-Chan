from typing import TypedDict, Optional

class TranscriptData(TypedDict):
    transcript: str
    mood: Optional[str]

class ServiceResponse(TypedDict):
    text: Optional[str]
    success: bool
    error: Optional[str] 