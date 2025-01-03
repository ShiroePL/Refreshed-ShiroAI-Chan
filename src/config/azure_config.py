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
    keys = {
        "madruss_groq_key": os.getenv('MADRUSS_GROQ_KEY'),
        "otaku_groq_key": os.getenv('OTAKU_GROQ_KEY'),
        "paid_groq_key": os.getenv('PAID_GROQ_KEY')
    }
    
    # Ensure at least one key is available
    if not any(keys.values()):
        raise ValueError("No Groq API keys found in environment variables")
    
    return keys 