import os
import azure.cognitiveservices.speech as speechsdk
import logging

logger = logging.getLogger("src.config.azure_config")

def get_speech_config():
    """Get Azure Speech SDK configuration from environment variables."""
    speech_key = os.getenv('SPEECH_KEY')
    service_region = os.getenv('SPEECH_REGION')
    
    if not speech_key or not service_region:
        raise ValueError("Azure Speech credentials not found in environment variables. "
                        "Please set SPEECH_KEY and SPEECH_REGION.")
    
    return speechsdk.SpeechConfig(
        subscription=speech_key,
        region=service_region
    )

def get_groq_api_keys():
    """Get Groq API keys from environment variables."""
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable not set")
    
    return [api_key] 