"""Claude API client for natural language processing"""

import anthropic
import logging
from typing import Optional, List, Dict, Generator
from collections import deque

from config.settings import (
    ANTHROPIC_API_KEY, CLAUDE_MODEL, CLAUDE_MAX_TOKENS,
    CLAUDE_TEMPERATURE, CONVERSATION_HISTORY_SIZE, DEBUG
)

logger = logging.getLogger(__name__)


class ClaudeClient:
    """Client for interacting with Claude API"""
    
    def __init__(self):
        if not ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not set in environment")
            
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.conversation_history = deque(maxlen=CONVERSATION_HISTORY_SIZE)
        self.system_prompt = self._get_system_prompt()
        
    def _get_system_prompt(self) -> str:
        """Get the system prompt for Claude"""
        return """You are Claude, a helpful AI assistant in a voice conversation. 
        Keep your responses concise and natural for spoken conversation. 
        Avoid using markdown, code blocks, or other formatting that doesn't work well in speech.
        Be friendly, helpful, and conversational."""
        
    def _prepare_messages(self, user_input: str) -> List[Dict]:
        """Prepare messages including conversation history"""
        messages = []
        
        # Add conversation history
        for msg in self.conversation_history:
            messages.append(msg)
            
        # Add current user message
        messages.append({
            "role": "user",
            "content": user_input
        })
        
        return messages
    
    def get_response(self, user_input: str) -> Optional[str]:
        """Get a response from Claude"""
        try:
            messages = self._prepare_messages(user_input)
            
            logger.debug(f"Sending to Claude: {user_input}")
            
            response = self.client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=CLAUDE_MAX_TOKENS,
                temperature=CLAUDE_TEMPERATURE,
                system=self.system_prompt,
                messages=messages
            )
            
            assistant_message = response.content[0].text
            
            # Update conversation history
            self.conversation_history.append({
                "role": "user",
                "content": user_input
            })
            self.conversation_history.append({
                "role": "assistant", 
                "content": assistant_message
            })
            
            logger.debug(f"Claude response: {assistant_message}")
            return assistant_message
            
        except anthropic.APIError as e:
            logger.error(f"Anthropic API error: {e}")
            return "I'm sorry, I encountered an API error. Please try again."
        except Exception as e:
            logger.error(f"Unexpected error getting Claude response: {e}")
            return "I'm sorry, something went wrong. Please try again."
    
    def get_streaming_response(self, user_input: str) -> Generator[str, None, None]:
        """Get a streaming response from Claude"""
        try:
            messages = self._prepare_messages(user_input)
            
            with self.client.messages.stream(
                model=CLAUDE_MODEL,
                max_tokens=CLAUDE_MAX_TOKENS,
                temperature=CLAUDE_TEMPERATURE,
                system=self.system_prompt,
                messages=messages
            ) as stream:
                full_response = ""
                for text in stream.text_stream:
                    full_response += text
                    yield text
                    
                # Update conversation history with complete response
                self.conversation_history.append({
                    "role": "user",
                    "content": user_input
                })
                self.conversation_history.append({
                    "role": "assistant",
                    "content": full_response
                })
                
        except Exception as e:
            logger.error(f"Error in streaming response: {e}")
            yield "I'm sorry, I encountered an error while responding."
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history.clear()
        logger.info("Conversation history cleared")
        
    def set_system_prompt(self, prompt: str):
        """Update the system prompt"""
        self.system_prompt = prompt
        logger.info("System prompt updated")


class ConversationManager:
    """Manages conversation flow and context"""
    
    def __init__(self):
        self.claude = ClaudeClient()
        self.is_active = False
        
    def start_conversation(self):
        """Start a new conversation"""
        self.is_active = True
        self.claude.clear_history()
        logger.info("Conversation started")
        
    def end_conversation(self):
        """End the current conversation"""
        self.is_active = False
        logger.info("Conversation ended")
        
    def process_input(self, text: str) -> Optional[str]:
        """Process user input and get response"""
        if not self.is_active:
            self.start_conversation()
            
        # Check for conversation control commands
        lower_text = text.lower().strip()
        
        if lower_text in ['goodbye', 'bye', 'exit', 'quit', 'stop']:
            self.end_conversation()
            return "Goodbye! It was nice talking with you."
        elif lower_text in ['clear history', 'new conversation', 'start over']:
            self.claude.clear_history()
            return "I've cleared our conversation history. Let's start fresh!"
        elif lower_text in ['help', 'what can you do']:
            return self._get_help_message()
            
        # Get Claude's response
        return self.claude.get_response(text)
    
    def _get_help_message(self) -> str:
        """Get help message"""
        return """I'm Claude, your AI assistant. You can:
        - Ask me questions about any topic
        - Have a natural conversation
        - Say 'clear history' to start a new conversation
        - Say 'goodbye' or 'stop' to end our conversation
        How can I help you today?"""