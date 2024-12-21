import azure.cognitiveservices.speech as speechsdk
import base64
import logging
from services.ai.config.azure_config import get_speech_config

logger = logging.getLogger(__name__)

class TTSService:
    def __init__(self):
        try:
            self.speech_config = get_speech_config()
            self.speech_synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config,
                audio_config=None
            )
            logger.info("TTS Service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize TTS service: {e}")
            raise

    async def text_to_speech(self, text: str) -> str | None:
        """Convert text to speech using Azure TTS."""
        try:
            logger.info("Preparing TTS request...")
            ssml = f"""<speak xmlns="http://www.w3.org/2001/10/synthesis" 
                          xmlns:mstts="http://www.w3.org/2001/mstts" 
                          xmlns:emo="http://www.w3.org/2009/10/emotionml" 
                          version="1.0" 
                          xml:lang="en-US">
                    <voice name="en-US-AshleyNeural">
                        <prosody rate="3%" pitch="21%">
                            {text}
                        </prosody>
                    </voice>
                </speak>"""
            
            logger.info("Calling speech synthesis...")
            result = self.speech_synthesizer.speak_ssml_async(ssml).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                logger.info("Speech synthesis completed successfully")
                audio_data = base64.b64encode(result.audio_data).decode('utf-8')
                logger.info(f"Audio data length: {len(audio_data)}")
                return audio_data
            else:
                logger.error(f"Speech synthesis failed: {result.reason}")
                return None
                
        except Exception as e:
            logger.error(f"Error in text_to_speech: {e}", exc_info=True)
            return None 