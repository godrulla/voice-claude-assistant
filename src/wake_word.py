"""Wake word detection using Porcupine"""

import logging
import threading
import time
from typing import Callable, Optional, List
import struct

from config.settings import (
    PORCUPINE_ACCESS_KEY, WAKE_WORDS, WAKE_WORD_SENSITIVITY,
    SAMPLE_RATE, DEBUG
)

logger = logging.getLogger(__name__)


class WakeWordDetector:
    """Wake word detection using Porcupine"""
    
    def __init__(self, callback: Callable[[], None]):
        self.callback = callback
        self.porcupine = None
        self.recorder = None
        self.running = False
        self.thread = None
        self.enabled = True
        
        # Try to initialize Porcupine
        self._init_porcupine()
        
    def _init_porcupine(self):
        """Initialize Porcupine wake word engine"""
        if not PORCUPINE_ACCESS_KEY:
            logger.warning("PORCUPINE_ACCESS_KEY not set. Wake word detection disabled.")
            return
            
        try:
            import pvporcupine
            from pvrecorder import PvRecorder
            
            # Use built-in keywords that are close to our wake words
            available_keywords = ['jarvis', 'computer', 'alexa']
            keywords = []
            
            # Map our wake words to available built-in keywords
            for wake_word in WAKE_WORDS:
                if 'claude' in wake_word.lower():
                    keywords.append('jarvis')  # Use Jarvis as substitute for Claude
                elif any(kw in wake_word.lower() for kw in available_keywords):
                    keywords.append(wake_word.lower())
                    
            if not keywords:
                keywords = ['jarvis']  # Default fallback
                
            logger.info(f"Initializing Porcupine with keywords: {keywords}")
            
            self.porcupine = pvporcupine.create(
                access_key=PORCUPINE_ACCESS_KEY,
                keywords=keywords,
                sensitivities=[WAKE_WORD_SENSITIVITY] * len(keywords)
            )
            
            self.recorder = PvRecorder(
                device_index=-1,
                frame_length=self.porcupine.frame_length
            )
            
            logger.info("Porcupine wake word detection initialized")
            
        except ImportError:
            logger.error("Porcupine not installed. Run: pip install pvporcupine pvrecorder")
        except Exception as e:
            logger.error(f"Failed to initialize Porcupine: {e}")
            logger.info("Wake word detection will be disabled")
            
    def start(self):
        """Start wake word detection"""
        if not self.porcupine:
            logger.warning("Wake word detection not available")
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._detection_loop)
        self.thread.start()
        
        logger.info("Wake word detection started")
        
    def stop(self):
        """Stop wake word detection"""
        self.running = False
        if self.thread:
            self.thread.join()
            
        if self.recorder:
            try:
                self.recorder.stop()
            except:
                pass
                
        logger.info("Wake word detection stopped")
        
    def _detection_loop(self):
        """Main detection loop"""
        try:
            self.recorder.start()
            logger.info("Listening for wake word...")
            
            while self.running:
                pcm = self.recorder.read()
                
                if self.enabled:
                    keyword_index = self.porcupine.process(pcm)
                    
                    if keyword_index >= 0:
                        logger.info(f"Wake word detected!")
                        self.callback()
                        
                        # Brief pause to avoid multiple triggers
                        time.sleep(0.5)
                        
        except Exception as e:
            logger.error(f"Error in wake word detection: {e}")
        finally:
            if self.recorder:
                try:
                    self.recorder.stop()
                except:
                    pass
                    
    def pause(self):
        """Temporarily disable wake word detection"""
        self.enabled = False
        logger.debug("Wake word detection paused")
        
    def resume(self):
        """Resume wake word detection"""
        self.enabled = True
        logger.debug("Wake word detection resumed")
        
    def cleanup(self):
        """Clean up resources"""
        self.stop()
        
        if self.porcupine:
            self.porcupine.delete()
            
        if self.recorder:
            self.recorder.delete()


class SimpleWakeWordDetector:
    """Simple wake word detector without Porcupine (fallback)"""
    
    def __init__(self, callback: Callable[[], None]):
        self.callback = callback
        self.running = False
        self.thread = None
        
    def start(self):
        """Start listening for keyboard trigger"""
        self.running = True
        self.thread = threading.Thread(target=self._listen_loop)
        self.thread.start()
        
        logger.info("Simple wake word detection started (Press SPACE to activate)")
        
    def stop(self):
        """Stop detection"""
        self.running = False
        if self.thread:
            self.thread.join()
            
    def _listen_loop(self):
        """Listen for keyboard input"""
        try:
            import sys
            import tty
            import termios
            
            # Save terminal settings
            old_settings = termios.tcgetattr(sys.stdin)
            
            try:
                # Set terminal to raw mode
                tty.setraw(sys.stdin.fileno())
                
                while self.running:
                    # Non-blocking read
                    char = sys.stdin.read(1)
                    
                    if char == ' ':  # Space bar
                        logger.info("Manual activation triggered")
                        self.callback()
                    elif char == 'q':  # Quit
                        self.running = False
                        break
                        
            finally:
                # Restore terminal settings
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                
        except Exception as e:
            logger.error(f"Error in simple wake word detector: {e}")
            
    def pause(self):
        """Pause detection"""
        pass
        
    def resume(self):
        """Resume detection"""
        pass
        
    def cleanup(self):
        """Clean up"""
        self.stop()


def create_wake_word_detector(callback: Callable[[], None]) -> Optional[WakeWordDetector]:
    """Create appropriate wake word detector"""
    try:
        # Try Porcupine first
        detector = WakeWordDetector(callback)
        if detector.porcupine:
            return detector
    except:
        pass
        
    # Fallback to simple detector
    logger.info("Using simple wake word detector (keyboard activation)")
    return SimpleWakeWordDetector(callback)