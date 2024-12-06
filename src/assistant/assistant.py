from src.config.azure_config import get_speech_config
import azure.cognitiveservices.speech as speechsdk
import base64
import io
from .response_handler import ResponseHandler
from src.utils.logging_config import handle_error
import logging

logger = logging.getLogger(__name__)

class SimpleAssistant:
    def __init__(self):
        try:
            self.listening = False
            self.last_command = ""
            self.response = ""
            self.running = True
            self.speech_config = get_speech_config()
            self.speech_synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config,
                audio_config=None  # We'll use raw audio output
            )
            self.response_handler = ResponseHandler()
            logger.info("Assistant initialized successfully")
        except Exception as e:
            handle_error(logger, e, "Assistant initialization")

    def get_response(self, command):
        """Get response from the response handler."""
        try:
            response_text = self.response_handler.handle_response(command, self)
            audio_data = self.text_to_speech(response_text)
            
            return {
                'text': response_text,
                'audio': audio_data
            }
        except Exception as e:
            handle_error(logger, e, "Getting assistant response")
            return {
                'text': "I encountered an error processing your request.",
                'audio': None
            }

    def text_to_speech(self, text):
        """Convert text to speech using Azure TTS."""
        try:
            # Use SSML with Ashley Neural voice and custom prosody
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
            
            # Get audio data
            result = self.speech_synthesizer.speak_ssml_async(ssml).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                # Convert audio data to base64 for sending to client
                audio_data = base64.b64encode(result.audio_data).decode('utf-8')
                return audio_data
            else:
                logger.error(f"Speech synthesis failed: {result.reason}")
                return None
                
        except Exception as e:
            handle_error(logger, e, "Text-to-speech conversion")
            return None 