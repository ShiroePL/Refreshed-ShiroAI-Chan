from src.config.azure_config import get_speech_config
import azure.cognitiveservices.speech as speechsdk
import base64
import io

class SimpleAssistant:
    def __init__(self):
        self.listening = False
        self.last_command = ""
        self.response = ""
        self.running = True
        self.speech_config = get_speech_config()
        self.speech_synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=self.speech_config,
            audio_config=None  # We'll use raw audio output
        )

    def get_response(self, command):
        """Get response from the response handler."""
        from .response_handler import handle_response
        response_text = handle_response(command, self)
        
        # Generate speech from response
        audio_data = self.text_to_speech(response_text)
        
        return {
            'text': response_text,
            'audio': audio_data
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
                print(f"Speech synthesis failed: {result.reason}")
                return None
                
        except Exception as e:
            print(f"Error in text_to_speech: {str(e)}")
            return None 