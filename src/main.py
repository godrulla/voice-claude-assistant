"""Main application for Voice Claude Assistant"""

import logging
import signal
import sys
import threading
import time
from typing import Optional
from colorama import init, Fore, Style

from src.audio_handler import AudioHandler
from src.speech_recognition import SpeechRecognizer
from src.claude_client import ConversationManager
from src.text_to_speech import TextToSpeech
from src.wake_word import create_wake_word_detector

from config.settings import DEBUG, LOG_LEVEL

# Initialize colorama for colored output
init()

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VoiceAssistant:
    """Main voice assistant application"""
    
    def __init__(self):
        self.audio_handler = AudioHandler()
        self.speech_recognizer = SpeechRecognizer()
        self.conversation_manager = ConversationManager()
        self.tts = TextToSpeech()
        self.wake_word_detector = None
        
        self.is_listening = False
        self.is_processing = False
        self.running = True
        
        # Initialize wake word detector
        self._init_wake_word()
        
    def _init_wake_word(self):
        """Initialize wake word detection"""
        self.wake_word_detector = create_wake_word_detector(
            callback=self.on_wake_word_detected
        )
        
    def on_wake_word_detected(self):
        """Called when wake word is detected"""
        if not self.is_listening and not self.is_processing:
            logger.info("Wake word detected!")
            self.start_listening()
            
    def start_listening(self):
        """Start listening for user input"""
        if self.is_listening or self.is_processing:
            return
            
        self.is_listening = True
        
        # Pause wake word detection
        if self.wake_word_detector:
            self.wake_word_detector.pause()
            
        # Visual feedback
        print(f"\n{Fore.GREEN}🎤 Listening... Speak now!{Style.RESET_ALL}")
        
        # Play activation sound
        self.tts.speak("Yes?", interrupt=True)
        
        # Start recording in separate thread
        threading.Thread(target=self._listening_thread).start()
        
    def _listening_thread(self):
        """Thread for handling listening and processing"""
        try:
            # Record audio
            self.audio_handler.start_stream()
            audio_data = self.audio_handler.record_until_silence()
            self.audio_handler.stop_stream()
            
            if not audio_data:
                print(f"{Fore.YELLOW}No speech detected.{Style.RESET_ALL}")
                self.is_listening = False
                if self.wake_word_detector:
                    self.wake_word_detector.resume()
                return
                
            # Process audio
            self.is_listening = False
            self.is_processing = True
            
            print(f"{Fore.CYAN}🔄 Processing...{Style.RESET_ALL}")
            
            # Speech to text
            text = self.speech_recognizer.recognize_speech(audio_data)
            
            if text:
                print(f"{Fore.BLUE}You: {text}{Style.RESET_ALL}")
                
                # Get Claude's response
                response = self.conversation_manager.process_input(text)
                
                if response:
                    print(f"{Fore.MAGENTA}Claude: {response}{Style.RESET_ALL}")
                    
                    # Text to speech
                    self.tts.speak(response)
                    
                    # Check if conversation ended
                    if not self.conversation_manager.is_active:
                        self.running = False
            else:
                print(f"{Fore.YELLOW}Sorry, I didn't catch that.{Style.RESET_ALL}")
                self.tts.speak("Sorry, I didn't catch that.")
                
        except Exception as e:
            logger.error(f"Error in listening thread: {e}")
            print(f"{Fore.RED}An error occurred. Please try again.{Style.RESET_ALL}")
            self.tts.speak("Sorry, something went wrong.")
            
        finally:
            self.is_processing = False
            
            # Resume wake word detection
            if self.wake_word_detector and self.running:
                time.sleep(1)  # Brief pause before resuming
                self.wake_word_detector.resume()
                
    def run(self):
        """Run the voice assistant"""
        print(f"\n{Fore.GREEN}🎙️  Voice Claude Assistant Started!{Style.RESET_ALL}")
        print(f"{Fore.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Style.RESET_ALL}")
        
        # Display instructions
        self._show_instructions()
        
        # Start wake word detection
        if self.wake_word_detector:
            self.wake_word_detector.start()
        else:
            print(f"{Fore.YELLOW}⚠️  Wake word detection not available.{Style.RESET_ALL}")
            
        # Play greeting
        self.tts.say_greeting()
        
        try:
            # Main loop
            while self.running:
                time.sleep(0.1)
                
                # Check for manual activation (Enter key)
                if sys.stdin in threading.select.select([sys.stdin], [], [], 0)[0]:
                    line = sys.stdin.readline()
                    if line.strip() == "":
                        self.start_listening()
                    elif line.strip().lower() in ['quit', 'exit', 'q']:
                        break
                        
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
            
        finally:
            self.cleanup()
            
    def _show_instructions(self):
        """Show usage instructions"""
        if self.wake_word_detector and hasattr(self.wake_word_detector, 'porcupine'):
            wake_instruction = "Say 'Hey Claude' or 'Jarvis'"
        else:
            wake_instruction = "Press SPACE"
            
        print(f"""
{Fore.WHITE}Instructions:{Style.RESET_ALL}
  • {wake_instruction} to activate
  • Press ENTER for manual activation
  • Say 'goodbye' or 'stop' to end conversation
  • Say 'clear history' to start fresh
  • Type 'quit' or press Ctrl+C to exit

{Fore.WHITE}Voice Commands:{Style.RESET_ALL}
  • Ask any question
  • Have natural conversations
  • Request help or information
  
{Fore.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Style.RESET_ALL}
        """)
        
    def cleanup(self):
        """Clean up resources"""
        logger.info("Shutting down Voice Assistant...")
        
        self.running = False
        
        # Stop components
        if self.wake_word_detector:
            self.wake_word_detector.cleanup()
            
        self.tts.stop()
        self.audio_handler.cleanup()
        
        print(f"\n{Fore.GREEN}👋 Goodbye!{Style.RESET_ALL}")
        

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print(f"\n{Fore.YELLOW}Shutting down...{Style.RESET_ALL}")
    sys.exit(0)


def main():
    """Main entry point"""
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Check for API key
        from config.settings import ANTHROPIC_API_KEY
        if not ANTHROPIC_API_KEY:
            print(f"{Fore.RED}Error: ANTHROPIC_API_KEY not set in config/.env{Style.RESET_ALL}")
            print(f"Please copy config/.env.example to config/.env and add your API key.")
            sys.exit(1)
            
        # Create and run assistant
        assistant = VoiceAssistant()
        assistant.run()
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"{Fore.RED}Fatal error: {e}{Style.RESET_ALL}")
        sys.exit(1)


if __name__ == "__main__":
    main()