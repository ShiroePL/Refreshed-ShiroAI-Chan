import os
import azure.cognitiveservices.speech as speechsdk

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