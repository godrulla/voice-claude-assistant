# Voice Claude Assistant

A hands-free voice interaction system for Claude AI that allows natural conversations using only your voice.

## Features

- 🎤 **Voice Input**: Speech-to-text using OpenAI Whisper (offline) or Google Speech Recognition
- 🔊 **Voice Output**: Natural text-to-speech with macOS native voices or gTTS
- 👂 **Wake Word Detection**: Activate with "Hey Claude" using Porcupine
- 💬 **Natural Conversations**: Powered by Claude's advanced language understanding
- 🔄 **Continuous Listening**: Hands-free operation with wake word activation
- 📝 **Conversation Memory**: Maintains context across multiple exchanges

## Prerequisites

- Python 3.9 or higher
- macOS (for native TTS) or any OS with gTTS support
- Microphone access
- Internet connection (for Claude API and Google STT)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/godrulla/voice-claude-assistant.git
cd voice-claude-assistant
```

2. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install system dependencies (macOS):
```bash
# For PyAudio
brew install portaudio
```

5. Configure API keys:
```bash
cp config/.env.example config/.env
# Edit config/.env and add your API keys:
# - ANTHROPIC_API_KEY (required)
# - PORCUPINE_ACCESS_KEY (optional, for wake word)
```

## Getting API Keys

### Anthropic API Key (Required)
1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Navigate to API Keys
4. Create a new key and copy it

### Porcupine Access Key (Optional)
1. Go to https://console.picovoice.ai/
2. Sign up for free account
3. Create a new project
4. Copy the access key

## Usage

1. Start the assistant:
```bash
python -m src.main
```

2. Interaction methods:
   - Say "Hey Claude" or "Jarvis" to activate (if Porcupine is configured)
   - Press SPACE for manual activation (fallback)
   - Press ENTER for immediate activation

3. Voice commands:
   - Ask any question naturally
   - Say "goodbye" or "stop" to end conversation
   - Say "clear history" to start a new conversation
   - Say "help" for assistance

## Configuration

Edit `config/.env` to customize:

- **STT_ENGINE**: Choose 'whisper' (offline) or 'google' (online)
- **WHISPER_MODEL**: Model size (tiny, base, small, medium, large)
- **TTS_ENGINE**: Choose 'macos', 'gtts', or 'pyttsx3'
- **TTS_VOICE**: Voice name (e.g., 'Samantha' for macOS)
- **WAKE_WORD_SENSITIVITY**: Adjust wake word sensitivity (0.0-1.0)
- **CLAUDE_MODEL**: Claude model to use
- **DEBUG**: Enable debug logging

## Troubleshooting

### No audio input detected
- Check microphone permissions in System Preferences
- Verify correct audio device: `python -c "import pyaudio; print(pyaudio.PyAudio().get_device_count())"`

### Wake word not working
- Ensure PORCUPINE_ACCESS_KEY is set correctly
- Try adjusting WAKE_WORD_SENSITIVITY
- Use manual activation (SPACE or ENTER) as fallback

### Speech recognition issues
- For Whisper: First run may be slow due to model download
- For Google: Requires internet connection
- Try speaking more clearly or adjusting microphone position

### macOS specific issues
- Grant terminal microphone access when prompted
- For Apple Silicon Macs: Some dependencies may need Rosetta 2

## Project Structure

```
voice-claude-assistant/
├── src/
│   ├── audio_handler.py      # Microphone and audio management
│   ├── speech_recognition.py # STT with Whisper/Google
│   ├── claude_client.py      # Claude API integration
│   ├── text_to_speech.py     # TTS engines
│   ├── wake_word.py          # Wake word detection
│   └── main.py               # Main application
├── config/
│   ├── settings.py           # Configuration loader
│   └── .env                  # API keys and settings
├── requirements.txt
└── README.md
```

## Performance Tips

1. **For lower latency**: Use Google STT instead of Whisper
2. **For offline use**: Use Whisper STT and macOS TTS
3. **For better accuracy**: Use larger Whisper models (requires more RAM)
4. **For natural voices**: Use gTTS with internet connection

## Privacy Note

- Whisper runs locally - audio never leaves your device
- Google STT sends audio to Google servers
- Claude API sends transcribed text to Anthropic
- No audio is stored permanently by the application

## License

MIT License

## Acknowledgments

- OpenAI Whisper for local speech recognition
- Picovoice Porcupine for wake word detection
- Anthropic for Claude AI
- Google for Speech Recognition API

---

Built by Armando Diaz Silverio