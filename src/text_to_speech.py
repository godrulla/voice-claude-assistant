"""Text-to-Speech implementation with multiple engine support"""

import os
import subprocess
import tempfile
import logging
from typing import Optional
from abc import ABC, abstractmethod
import threading
import queue

from config.settings import (
    TTS_ENGINE, TTS_VOICE, TTS_RATE, 
    LANGUAGE, DEBUG
)

logger = logging.getLogger(__name__)


class TTSEngine(ABC):
    """Abstract base class for TTS engines"""
    
    @abstractmethod
    def speak(self, text: str) -> bool:
        """Convert text to speech"""
        pass
        
    @abstractmethod
    def stop(self):
        """Stop current speech"""
        pass


class MacOSTTS(TTSEngine):
    """macOS native text-to-speech using 'say' command"""
    
    def __init__(self):
        self.process = None
        self.voice = TTS_VOICE or "Samantha"
        self.rate = TTS_RATE or 200
        
    def speak(self, text: str) -> bool:
        """Speak text using macOS say command"""
        try:
            # Stop any ongoing speech
            self.stop()
            
            # Clean text for speech
            text = self._clean_text(text)
            
            # Build command
            cmd = ["say", "-v", self.voice, "-r", str(self.rate)]
            
            logger.debug(f"Speaking with macOS: {text}")
            
            # Start speech process
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Send text to process
            self.process.communicate(input=text.encode('utf-8'))
            
            return True
            
        except Exception as e:
            logger.error(f"macOS TTS error: {e}")
            return False
            
    def stop(self):
        """Stop current speech"""
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.process = None
            
    def _clean_text(self, text: str) -> str:
        """Clean text for better speech output"""
        # Remove markdown-style formatting
        text = text.replace('*', '')
        text = text.replace('_', '')
        text = text.replace('`', '')
        text = text.replace('#', '')
        
        return text


class GTTS_TTS(TTSEngine):
    """Google Text-to-Speech engine"""
    
    def __init__(self):
        self.playing_thread = None
        self.should_stop = False
        
    def speak(self, text: str) -> bool:
        """Speak text using gTTS"""
        try:
            from gtts import gTTS
            import pygame
            
            # Initialize pygame mixer
            pygame.mixer.init()
            
            # Stop any ongoing speech
            self.stop()
            
            # Clean text
            text = self._clean_text(text)
            
            logger.debug(f"Speaking with gTTS: {text}")
            
            # Create gTTS object
            tts = gTTS(text=text, lang=LANGUAGE, slow=False)
            
            # Save to temporary file
            fd, temp_file = tempfile.mkstemp(suffix='.mp3')
            os.close(fd)
            tts.save(temp_file)
            
            # Play audio in separate thread
            self.should_stop = False
            self.playing_thread = threading.Thread(
                target=self._play_audio,
                args=(temp_file,)
            )
            self.playing_thread.start()
            
            return True
            
        except ImportError:
            logger.error("gTTS not installed. Run: pip install gtts pygame")
            return False
        except Exception as e:
            logger.error(f"gTTS error: {e}")
            return False
            
    def _play_audio(self, filename: str):
        """Play audio file"""
        try:
            import pygame
            
            pygame.mixer.music.load(filename)
            pygame.mixer.music.play()
            
            # Wait for playback to complete
            while pygame.mixer.music.get_busy() and not self.should_stop:
                pygame.time.Clock().tick(10)
                
            pygame.mixer.music.stop()
            
            # Clean up temp file
            try:
                os.unlink(filename)
            except:
                pass
                
        except Exception as e:
            logger.error(f"Error playing audio: {e}")
            
    def stop(self):
        """Stop current speech"""
        self.should_stop = True
        try:
            import pygame
            pygame.mixer.music.stop()
        except:
            pass
            
    def _clean_text(self, text: str) -> str:
        """Clean text for better speech output"""
        # Remove markdown-style formatting
        text = text.replace('*', '')
        text = text.replace('_', '')
        text = text.replace('`', '')
        text = text.replace('#', '')
        
        return text


class Pyttsx3TTS(TTSEngine):
    """Pyttsx3 offline text-to-speech engine"""
    
    def __init__(self):
        self.engine = None
        self._init_engine()
        
    def _init_engine(self):
        """Initialize pyttsx3 engine"""
        try:
            import pyttsx3
            self.engine = pyttsx3.init()
            
            # Configure voice
            voices = self.engine.getProperty('voices')
            for voice in voices:
                if TTS_VOICE.lower() in voice.name.lower():
                    self.engine.setProperty('voice', voice.id)
                    break
                    
            # Set speech rate
            self.engine.setProperty('rate', TTS_RATE)
            
        except ImportError:
            logger.error("pyttsx3 not installed. Run: pip install pyttsx3")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize pyttsx3: {e}")
            raise
            
    def speak(self, text: str) -> bool:
        """Speak text using pyttsx3"""
        if not self.engine:
            return False
            
        try:
            text = self._clean_text(text)
            logger.debug(f"Speaking with pyttsx3: {text}")
            
            self.engine.say(text)
            self.engine.runAndWait()
            
            return True
            
        except Exception as e:
            logger.error(f"pyttsx3 error: {e}")
            return False
            
    def stop(self):
        """Stop current speech"""
        if self.engine:
            try:
                self.engine.stop()
            except:
                pass
                
    def _clean_text(self, text: str) -> str:
        """Clean text for better speech output"""
        text = text.replace('*', '')
        text = text.replace('_', '')
        text = text.replace('`', '')
        text = text.replace('#', '')
        
        return text


class TextToSpeech:
    """Main text-to-speech interface"""
    
    def __init__(self):
        self.engine = self._init_engine()
        self.queue = queue.Queue()
        self.speaking_thread = None
        self.should_stop = False
        
    def _init_engine(self) -> Optional[TTSEngine]:
        """Initialize the appropriate TTS engine"""
        engine_map = {
            'macos': MacOSTTS,
            'gtts': GTTS_TTS,
            'pyttsx3': Pyttsx3TTS
        }
        
        # Try primary engine
        if TTS_ENGINE in engine_map:
            try:
                logger.info(f"Initializing {TTS_ENGINE} TTS engine")
                return engine_map[TTS_ENGINE]()
            except Exception as e:
                logger.error(f"Failed to initialize {TTS_ENGINE}: {e}")
                
        # Try fallback engines
        for name, engine_class in engine_map.items():
            if name != TTS_ENGINE:
                try:
                    logger.info(f"Trying fallback TTS engine: {name}")
                    return engine_class()
                except:
                    continue
                    
        logger.error("No TTS engine could be initialized")
        return None
        
    def speak(self, text: str, interrupt: bool = True):
        """Speak text"""
        if not self.engine:
            logger.error("No TTS engine available")
            return
            
        if interrupt:
            self.stop()
            
        self.queue.put(text)
        
        if not self.speaking_thread or not self.speaking_thread.is_alive():
            self.should_stop = False
            self.speaking_thread = threading.Thread(target=self._speaking_loop)
            self.speaking_thread.start()
            
    def _speaking_loop(self):
        """Process speech queue"""
        while not self.should_stop:
            try:
                text = self.queue.get(timeout=0.1)
                if text:
                    self.engine.speak(text)
            except queue.Empty:
                if self.queue.empty():
                    break
                    
    def stop(self):
        """Stop current speech"""
        self.should_stop = True
        
        # Clear queue
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except:
                pass
                
        if self.engine:
            self.engine.stop()
            
    def say_greeting(self):
        """Speak a greeting message"""
        greetings = [
            "Hello! I'm Claude, your AI assistant. How can I help you today?",
            "Hi there! I'm ready to help. What would you like to talk about?",
            "Hello! I'm Claude. Feel free to ask me anything."
        ]
        
        import random
        self.speak(random.choice(greetings))