"""Configuration settings for Voice Claude Assistant"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

# API Keys
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
PORCUPINE_ACCESS_KEY = os.getenv('PORCUPINE_ACCESS_KEY')

# Claude settings
CLAUDE_MODEL = os.getenv('CLAUDE_MODEL', 'claude-3-5-sonnet-20241022')
CLAUDE_MAX_TOKENS = int(os.getenv('CLAUDE_MAX_TOKENS', '1000'))
CLAUDE_TEMPERATURE = float(os.getenv('CLAUDE_TEMPERATURE', '0.7'))

# Speech recognition settings
STT_ENGINE = os.getenv('STT_ENGINE', 'whisper')  # 'whisper' or 'google'
WHISPER_MODEL = os.getenv('WHISPER_MODEL', 'base')  # tiny, base, small, medium, large
LANGUAGE = os.getenv('LANGUAGE', 'en')

# Text-to-speech settings
TTS_ENGINE = os.getenv('TTS_ENGINE', 'macos')  # 'macos', 'gtts', or 'pyttsx3'
TTS_VOICE = os.getenv('TTS_VOICE', 'Samantha')  # macOS voice name
TTS_RATE = int(os.getenv('TTS_RATE', '200'))  # Speech rate

# Wake word settings
WAKE_WORDS = ['hey claude', 'claude']
WAKE_WORD_SENSITIVITY = float(os.getenv('WAKE_WORD_SENSITIVITY', '0.5'))

# Audio settings
SAMPLE_RATE = 16000
CHUNK_SIZE = 1024
AUDIO_TIMEOUT = int(os.getenv('AUDIO_TIMEOUT', '30'))  # seconds
SILENCE_THRESHOLD = int(os.getenv('SILENCE_THRESHOLD', '500'))

# Application settings
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
CONVERSATION_HISTORY_SIZE = int(os.getenv('CONVERSATION_HISTORY_SIZE', '10'))