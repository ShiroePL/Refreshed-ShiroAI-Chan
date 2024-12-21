import os
import azure.cognitiveservices.speech as speechsdk
import logging

logger = logging.getLogger(__name__)

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
    api_keys_str = os.getenv('GROQ_API_KEY')
    
    if not api_keys_str:
        raise ValueError("Groq API keys not found in environment variables. "
                        "Please set GROQ_API_KEY as comma-separated values.")
    
    # Split and clean the keys
    keys = [key.strip() for key in api_keys_str.split(',') if key.strip()]
    if not keys:
        raise ValueError("No valid Groq API keys found after processing")
    
    logger.debug(f"Loaded {len(keys)} Groq API key(s)")
    return keys 