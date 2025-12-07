"""
Withdrawal detection system using action brackets and AI analysis.
Determines if player has left the conversation based on bracketed actions.
"""

from typing import Tuple
import re
from openrouter_client import GenerativeModel
from config import Config


class WithdrawalDetector:
    """Detects when a player has withdrawn from the conversation using action brackets."""
    
    def __init__(self):
        """Initialize the withdrawal detector."""
        self.model = None
    
    def get_or_create_model(self):
        """Get or create the AI model."""
        if self.model is None:
            self.model = GenerativeModel(Config.DEFAULT_MODEL)
        return self.model
    
    def extract_action_from_brackets(self, message: str) -> Tuple[str, str]:
        """
        Extract action from brackets [action] in the message.
        
        Args:
            message: The player's message
            
        Returns:
            Tuple of (dialogue, action) where action is empty string if no brackets found
        """
        # Find content in brackets using regex
        bracket_pattern = r'\[([^\]]+)\]'
        matches = re.findall(bracket_pattern, message)
        
        if not matches:
            return (message, "")
        
        # Get the last bracketed action (most recent action)
        action = matches[-1].strip()
        
        # Remove brackets from dialogue
        dialogue = re.sub(bracket_pattern, '', message).strip()
        
        return (dialogue, action)
    
    def is_leaving_action(self, action: str) -> bool:
        """
        Use AI to determine if the bracketed action means the player is leaving.
        
        Args:
            action: The action text from brackets
            
        Returns:
            True if the action indicates leaving/departing, False otherwise
        """
        if not action:
            return False
        
        # Use AI to analyze the action
        try:
            prompt = f"""Analyze this action and determine if it means the person is LEAVING the current location/conversation or DEPARTING from the room.

ACTION: "{action}"

Consider:
- "heads upstairs", "goes to bed", "walks away", "exits room" = LEAVING (return YES)
- "coughing", "sits down", "picks up book", "adjusts glasses" = NOT LEAVING (return NO)
- "starts walking upstairs", "begins to leave" = LEAVING (return YES)
- Physical departure from the current space = LEAVING
- Actions done while staying in place = NOT LEAVING

Answer ONLY with: YES or NO

Answer:"""
            
            model = self.get_or_create_model()
            response = model.generate_content(prompt)
            
            answer = response.text.strip().upper()
            return 'YES' in answer
            
        except Exception as e:
            # On error, assume not leaving (conservative approach)
            print(f"⚠️  AI analysis failed: {e}")
            return False
    
    def detect_withdrawal(self, message: str, player_name: str) -> Tuple[bool, str, str]:
        """
        Detect if player is withdrawing from conversation.
        
        Args:
            message: The player's message
            player_name: Name of the player
            
        Returns:
            Tuple of (is_withdrawing, dialogue, action_description)
        """
        # Extract action from brackets
        dialogue, action = self.extract_action_from_brackets(message)
        
        # Check if action indicates leaving
        is_leaving = self.is_leaving_action(action)
        
        return (is_leaving, dialogue, action)
    
    def format_withdrawal_message(self, player_name: str, action: str) -> str:
        """
        Format a nice withdrawal message.
        
        Args:
            player_name: Name of the player
            action: The leaving action
            
        Returns:
            Formatted withdrawal message
        """
        return f"\n💤 {player_name} {action}...\n🗣️  The AI characters continue talking...\n"
