# Shiro AI Assistant

A voice-enabled AI assistant with an anime-inspired personality. Shiro is a bubbly and quirky virtual character who helps with various tasks while maintaining a fun, engaging conversation style.

## Features

- Voice interaction using browser's Speech Recognition
- Text-to-speech responses using Azure Speech Services
- AI-powered conversations using Groq's LLaMA model
- Anime-inspired personality with cat-like speech patterns
- Web interface for easy interaction
- Global Push-to-Talk functionality using Backtick/Tilde Key
- Toggle listening mode for hands-free operation

## Voice Control Features

### Push-to-Talk (Backtick/Tilde Key)
The assistant includes a global Push-to-Talk feature that works even when the browser window is not focused:
- Press and hold the backtick key (`) (the key before 1 on keyboard) to activate voice input
- Release the key to stop recording and process your speech
- Works in background when browser is minimized

**Requirements for Background Operation:**
1. Browser must be running in the background
2. Backtick key (`) should not be captured by other applications
3. Some browsers may require additional permissions for background access
4. For optimal performance, keep the browser running and avoid system sleep mode

### Other Voice Controls
- Toggle Listen button for continuous listening mode
- Voice On/Off toggle for assistant's speech
- Stop Speaking button to interrupt assistant's current speech

## Tech Stack

- Python (Flask)
- JavaScript
- Azure Speech Services
- Groq API
- WebSocket for real-time communication

## Requirements
- Python 3.7+
- Modern web browser
- Administrative privileges (for global hotkey functionality)

## Local Setup

1. Clone the repository
2. Create a `.env` file with required API keys:
   - `SPEECH_KEY` - Azure Speech Service key
   - `SPEECH_REGION` - Azure Speech Service region
   - `GROQ_API_KEY` - Comma-separated Groq API keys
3. Install dependencies: `pip install -r requirements.txt`
4. Run with administrative privileges (required for global hotkeys):
   - Windows: Right-click Python/terminal and "Run as Administrator"
   - Linux: `sudo python app.py`
   - Mac: `sudo python app.py`
5. Open browser at `http://localhost:5000`

## Usage

The assistant can be controlled in multiple ways:
1. Using the web interface buttons
2. Using Backtick/Tilde Key for Push-to-Talk (works globally)
3. Using Toggle Listen for hands-free operation

For the best experience, ensure no other applications are using the Backtick/Tilde Key and keep the browser running in the background.
