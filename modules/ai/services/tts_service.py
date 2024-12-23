import azure.cognitiveservices.speech as speechsdk
import base64
import logging
from src.config.azure_config import get_speech_config

logger = logging.getLogger("modules.ai.services.tts_service")

class TTSService:
    def __init__(self):
        self.speech_config = get_speech_config()
        self.speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=self.speech_config)

    async def text_to_speech(self, text: str) -> str:
        try:
            # Get audio data as bytes
            result = self.speech_synthesizer.speak_text_async(text).get()
            
            if result.result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                # Properly encode audio data to base64
                audio_data = base64.b64encode(result.audio_data).decode('utf-8')
                logger.info(f"Audio synthesis successful, encoded length: {len(audio_data)}")
                return audio_data
            else:
                logger.error(f"Speech synthesis failed: {result.result.reason}")
                return None
                
        except Exception as e:
            logger.error(f"TTS error: {str(e)}")
            return None 