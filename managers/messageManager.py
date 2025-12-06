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
    
    def create_message(self, speaker: str, content: str, emotion: Optional[str] = None) -> Message:
        """Create a new message instance."""
        return Message(speaker=speaker, content=content, emotion=emotion)
    
    def add_message(
        self,
        scene: MessageHistory,
        message: Message
    ) -> Message:
        """
        Add a message to the scene and update participants.
        
        Args:
            scene: MessageHistory instance to add message to
            message: Message instance to add
            
        Returns:
            The added Message
        """
        scene.messages.append(message)
        
        # Update participants if new speaker
        if message.speaker not in scene.participants:
            scene.participants.append(message.speaker)
        
        return message
    
    def get_recent_messages(self, scene: MessageHistory, n: int = 10) -> List[Message]:
        """
        Get the n most recent messages from history.
        
        Args:
            scene: MessageHistory instance to retrieve from
            n: Number of recent messages
            
        Returns:
            List of recent messages
        """
        return scene.messages[-n:] if len(scene.messages) > n else scene.messages
    
    def get_messages_by_speaker(self, scene: MessageHistory, speaker: str) -> List[Message]:
        """Get all messages from a specific speaker."""
        return [msg for msg in scene.messages if msg.speaker == speaker]
    
    def get_messages_with_emotion(self, scene: MessageHistory, emotion: str) -> List[Message]:
        """Get all messages with a specific emotion."""
        return [msg for msg in scene.messages if msg.emotion == emotion]
    
    def get_message_count(self, scene: MessageHistory) -> int:
        """Get total number of messages."""
        return len(scene.messages)