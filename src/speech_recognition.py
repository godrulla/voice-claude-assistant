"""Speech-to-Text implementation with multiple engine support"""

import os
import tempfile
import logging
from typing import Optional, Union
import speech_recognition as sr
from abc import ABC, abstractmethod

from config.settings import (
    STT_ENGINE, WHISPER_MODEL, LANGUAGE, 
    SAMPLE_RATE, DEBUG
)

logger = logging.getLogger(__name__)


class STTEngine(ABC):
    """Abstract base class for STT engines"""
    
    @abstractmethod
    def transcribe(self, audio_data: Union[bytes, str]) -> Optional[str]:
        """Transcribe audio to text"""
        pass


class WhisperSTT(STTEngine):
    """OpenAI Whisper speech-to-text engine"""
    
    def __init__(self):
        self.model = None
        self._load_model()
        
    def _load_model(self):
        """Load Whisper model"""
        try:
            import whisper
            logger.info(f"Loading Whisper model: {WHISPER_MODEL}")
            self.model = whisper.load_model(WHISPER_MODEL)
            logger.info("Whisper model loaded successfully")
        except ImportError:
            logger.error("Whisper not installed. Run: pip install openai-whisper")
            raise
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise
            
    def transcribe(self, audio_data: Union[bytes, str]) -> Optional[str]:
        """Transcribe audio using Whisper"""
        if not self.model:
            return None
            
        try:
            # If audio_data is bytes, save to temporary file
            if isinstance(audio_data, bytes):
                fd, temp_path = tempfile.mkstemp(suffix='.wav')
                os.close(fd)
                
                # Import audio_handler to save audio
                from src.audio_handler import AudioHandler
                handler = AudioHandler()
                handler.save_audio(audio_data, temp_path)
                handler.cleanup()
                
                audio_path = temp_path
                cleanup = True
            else:
                audio_path = audio_data
                cleanup = False
                
            # Transcribe
            result = self.model.transcribe(
                audio_path,
                language=LANGUAGE,
                fp16=False  # Disable for compatibility
            )
            
            # Cleanup temporary file
            if cleanup:
                os.unlink(audio_path)
                
            text = result['text'].strip()
            logger.debug(f"Whisper transcription: {text}")
            return text
            
        except Exception as e:
            logger.error(f"Whisper transcription error: {e}")
            return None


class GoogleSTT(STTEngine):
    """Google Speech Recognition engine"""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        
    def transcribe(self, audio_data: Union[bytes, str]) -> Optional[str]:
        """Transcribe audio using Google Speech Recognition"""
        try:
            # Convert audio data to AudioData object
            if isinstance(audio_data, bytes):
                audio = sr.AudioData(audio_data, SAMPLE_RATE, 2)
            else:
                # If file path, load the audio
                with sr.AudioFile(audio_data) as source:
                    audio = self.recognizer.record(source)
                    
            # Transcribe
            text = self.recognizer.recognize_google(
                audio,
                language=LANGUAGE
            )
            
            logger.debug(f"Google transcription: {text}")
            return text
            
        except sr.UnknownValueError:
            logger.warning("Google Speech Recognition could not understand audio")
            return None
        except sr.RequestError as e:
            logger.error(f"Google Speech Recognition error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in Google STT: {e}")
            return None


class HybridSTT(STTEngine):
    """Hybrid STT that tries multiple engines"""
    
    def __init__(self):
        self.engines = []
        
        # Initialize primary engine
        if STT_ENGINE == 'whisper':
            try:
                self.engines.append(('whisper', WhisperSTT()))
            except:
                logger.warning("Failed to initialize Whisper, falling back to Google")
                
        # Always add Google as fallback
        self.engines.append(('google', GoogleSTT()))
        
    def transcribe(self, audio_data: Union[bytes, str]) -> Optional[str]:
        """Try multiple engines until one succeeds"""
        for name, engine in self.engines:
            try:
                logger.debug(f"Trying {name} engine...")
                text = engine.transcribe(audio_data)
                if text:
                    logger.info(f"Successfully transcribed with {name}")
                    return text
            except Exception as e:
                logger.error(f"{name} engine failed: {e}")
                continue
                
        logger.error("All STT engines failed")
        return None


class SpeechRecognizer:
    """Main speech recognition interface"""
    
    def __init__(self):
        self.engine = HybridSTT()
        
    def recognize_speech(self, audio_data: Union[bytes, str]) -> Optional[str]:
        """Recognize speech from audio data or file"""
        if not audio_data:
            return None
            
        logger.info("Starting speech recognition...")
        text = self.engine.transcribe(audio_data)
        
        if text:
            logger.info(f"Recognized: {text}")
        else:
            logger.warning("No speech recognized")
            
        return text
    
    def recognize_from_microphone(self) -> Optional[str]:
        """Record from microphone and recognize speech"""
        from src.audio_handler import AudioHandler
        
        handler = AudioHandler()
        handler.start_stream()
        
        logger.info("Listening... Speak now!")
        audio_data = handler.record_until_silence()
        
        handler.cleanup()
        
        if audio_data:
            return self.recognize_speech(audio_data)
        return None