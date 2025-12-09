"""
Manager for message-related operations.
"""

from typing import List, Dict, Optional
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from data_models import Message, MessageHistory


class MessageManager:
    """Manager for message-related operations."""
    
    def __init__(self):
        """Initialize MessageManager."""
        pass
    
    def create_message(
        self, 
        speaker: str, 
        content: str, 
        action_description: str
    ) -> Message:
        """Create a new message instance."""
        return Message(
            speaker=speaker, 
            content=content, 
            action_description=action_description
        )
    
    def add_message(
        self,
        message_history: MessageHistory,
        message: Message
    ) -> Message:
        """
        Add a message to the message_history and update participants.
        
        Args:
            message_history: MessageHistory instance to add message to
            message: Message instance to add
            
        Returns:
            The added Message
        """
        message_history.messages.append(message)
        
        if message.speaker not in message_history.participants:
            message_history.participants.append(message.speaker)
        
        return message
    
    def get_recent_messages(self, message_history: MessageHistory, n: int = 10) -> List[Message]:
        """
        Get the n most recent messages from history.
        
        Args:
            message_history: MessageHistory instance to retrieve from
            n: Number of recent messages
            
        Returns:
            List of recent messages
        """
        return message_history.messages[-n:] if len(message_history.messages) > n else message_history.messages
    
    def create_message_history(
        self,
        title: Optional[str] = None,
        scene_description: Optional[str] = None,
        participants: Optional[List[str]] = None,
        visible_to_user: bool = True,
        location: Optional[str] = None
    ) -> MessageHistory:
        """
        Create a new message history.
        
        Args:
            title: Optional conversation title (e.g., 'Midnight Planning')
            scene_description: Optional description of the scene or context
            location: Optional location where conversation took place
            participants: Optional initial participants list
            visible_to_user: Whether user can view this conversation (default True)
            
        Returns:
            New MessageHistory instance
        """
        
        return MessageHistory(
            title=title,
            scene_description=scene_description,
            location=location,
            participants=participants,
            visible_to_user=visible_to_user,
            location = location
        )
    