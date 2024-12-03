# Shiro AI Assistant

A voice-enabled AI assistant with an anime-inspired personality. Shiro is a bubbly and quirky virtual character who helps with various tasks while maintaining a fun, engaging conversation style.

## Features

- Voice interaction using browser's Speech Recognition
- Text-to-speech responses using Azure Speech Services
- AI-powered conversations using Groq's LLaMA model
- Anime-inspired personality with cat-like speech patterns
- Web interface for easy interaction

## Tech Stack

- Python (Flask)
- JavaScript
- Azure Speech Services
- Groq API
- WebSocket for real-time communication

## Local Setup

1. Clone the repository
2. Create a `.env` file with required API keys:
   - `SPEECH_KEY` - Azure Speech Service key
   - `SPEECH_REGION` - Azure Speech Service region
   - `GROQ_API_KEY` - Comma-separated Groq API keys
3. Install dependencies
4. Run `python app.py`
5. Open browser at `http://localhost:5000`

## Usage

Click "Start Listening" to begin voice interaction with Shiro. She'll respond both in text and voice, maintaining her characteristic anime-inspired personality.
