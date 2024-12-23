import os
import sys
import logging
import time
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import numpy
    import torch
    from transformers import pipeline
    from transformers.utils import is_flash_attn_2_available
except ImportError as e:
    logger.error(f"Failed to import required packages: {str(e)}")
    logger.info("Please ensure you have the correct versions installed:")
    logger.info("pip install numpy==1.24.3 torch transformers")
    sys.exit(1)

class WhisperTranscriber:
    def __init__(self, device="cuda:0"):
        """
        Initialize the WhisperTranscriber with the model loaded and ready
        """
        self.device = device
        logger.info("Initializing Whisper model...")
        start_time = time.time()
        try:
            self.pipe = pipeline(
                "automatic-speech-recognition",
                model="openai/whisper-medium.en",
                torch_dtype=torch.float16,
                device=self.device,
                model_kwargs={"attn_implementation": "flash_attention_2"} if is_flash_attn_2_available() else {"attn_implementation": "sdpa"},
            )
            load_time = time.time() - start_time
            logger.info(f"Whisper model loaded successfully in {load_time:.2f} seconds!")
        except Exception as e:
            logger.error(f"Failed to initialize Whisper model: {str(e)}")
            raise

    def transcribe(self, audio_path):
        """
        Transcribe a single audio file
        """
        try:
            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"Audio file not found: {audio_path}")
            
            # Get file size
            file_size = os.path.getsize(audio_path) / (1024 * 1024)  # Convert to MB
            
            logger.info(f"Transcribing {audio_path} (Size: {file_size:.2f} MB)...")
            start_time = time.time()
            
            outputs = self.pipe(
                audio_path,
                chunk_length_s=30,
                batch_size=24,
                return_timestamps=True,
            )
            
            transcription_time = time.time() - start_time
            logger.info(f"Transcription completed in {transcription_time:.2f} seconds!")
            
            # Calculate processing speed
            speed = file_size / transcription_time
            logger.info(f"Processing speed: {speed:.2f} MB/s")
            
            return outputs, transcription_time

        except Exception as e:
            logger.error(f"Error during transcription: {str(e)}")
            raise

    def __call__(self, audio_path):
        """
        Allow the class to be called directly like a function
        """
        return self.transcribe(audio_path)

def main():
    try:
        logger.info("Initializing Whisper Transcription Service...")
        transcriber = WhisperTranscriber()
        logger.info("Service ready! Model is loaded and waiting for input.")
        logger.info('Enter the path to a WAV file to transcribe (or type "exit" to quit)')

        # Keep track of all transcriptions
        transcription_stats = []

        while True:
            try:
                # Get input from user
                audio_path = input("\nEnter WAV file path: ").strip()
                
                # Check for exit command
                if audio_path.lower() in ['exit', 'quit', 'q']:
                    if transcription_stats:
                        # Show summary statistics
                        total_files = len(transcription_stats)
                        avg_time = sum(t for _, t in transcription_stats) / total_files
                        print("\nTranscription Statistics:")
                        print("-" * 50)
                        print(f"Total files processed: {total_files}")
                        print(f"Average processing time: {avg_time:.2f} seconds")
                        print(f"Fastest time: {min(t for _, t in transcription_stats):.2f} seconds")
                        print(f"Slowest time: {max(t for _, t in transcription_stats):.2f} seconds")
                        print("-" * 50)
                    logger.info("Shutting down transcription service...")
                    break

                # Process the file
                if audio_path:
                    result, proc_time = transcriber(audio_path)
                    transcription_stats.append((audio_path, proc_time))
                    
                    print("\nTranscription Result:")
                    print("-" * 50)
                    print(result)
                    print("-" * 50)
                    print(f"Processing time: {proc_time:.2f} seconds")
                else:
                    logger.warning("Please enter a valid file path")

            except FileNotFoundError:
                logger.error("File not found. Please check the path and try again.")
            except Exception as e:
                logger.error(f"Error processing file: {str(e)}")
                logger.info("You can try another file or type 'exit' to quit")

    except KeyboardInterrupt:
        logger.info("\nShutting down transcription service...")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())