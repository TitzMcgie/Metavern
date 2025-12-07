"""
Manager for scene-related operations.
"""

from typing import List, Optional
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from data_models import MessageHistory


class SceneManager:
    """Manager for conversation history operations."""
    
    def __init__(self,history: Optional[MessageHistory] = None):
        """
        Initialize SceneManager.
        """
        self.history = history
        # Store location and plot separately since MessageHistory doesn't have these fields
        self.location: Optional[str] = None
        self.plot: Optional[str] = None
    
    def create_scene(
        self,
        title: Optional[str] = None,
        plot: Optional[str] = None,
        location: Optional[str] = None,
        participants: Optional[List[str]] = None
    ) -> MessageHistory:
        """
        Create a new scene.
        
        Args:
            title: Optional scene title
            plot: Optional plot/context description
            location: Optional location
            participants: Optional initial participants list
            
        Returns:
            New MessageHistory instance
        """
        # Combine plot and location into scene_description
        scene_desc_parts = []
        if location:
            scene_desc_parts.append(f"Location: {location}")
        if plot:
            scene_desc_parts.append(plot)
        scene_description = " - ".join(scene_desc_parts) if scene_desc_parts else None
        
        self.history = MessageHistory(
            title=title,
            scene_description=scene_description,
            participants=participants or []
        )
        self.location = location
        self.plot = plot
        return self.history
    
    def add_participant(self, participant: str) -> None:
        """Add a participant to the scene."""
        if self.history and participant not in self.history.participants:
            self.history.participants.append(participant)
    
    def remove_participant(self, participant: str) -> None:
        """Remove a participant from the scene."""
        if self.history and participant in self.history.participants:
            self.history.participants.remove(participant)
    
    def update_summary(self, summary: str) -> None:
        """Update the scene summary."""
        if self.history:
            self.history.conversation_summary = summary
    
    def update_title(self, title: str) -> None:
        """Update the scene title."""
        if self.history:
            self.history.title = title
    
    def update_plot(self, plot: str) -> None:
        """Update the scene plot."""
        self.plot = plot
        self._update_scene_description()
    
    def update_location(self, location: str) -> None:
        """Update the scene location."""
        self.location = location
        self._update_scene_description()
    
    def _update_scene_description(self) -> None:
        """Internal method to update scene_description from plot and location."""
        if self.history:
            scene_desc_parts = []
            if self.location:
                scene_desc_parts.append(f"Location: {self.location}")
            if self.plot:
                scene_desc_parts.append(self.plot)
            self.history.scene_description = " - ".join(scene_desc_parts) if scene_desc_parts else None
    
    def get_message_count(self) -> int:
        """Get total number of messages."""
        return len(self.history.messages) if self.history else 0
    
    def clear_messages(self) -> None:
        """Clear all messages from history."""
        if self.history:
            self.history.messages.clear()
    
    def to_dict(self) -> dict:
        """Convert the scene to a dictionary."""
        if self.history:
            return self.history.model_dump()
        return {}
    
    def from_dict(self, data: dict) -> MessageHistory:
        """
        Load a scene from a dictionary.
        
        Args:
            data: Dictionary containing scene data
            
        Returns:
            MessageHistory object restored from data
        """
        # Use Pydantic's model_validate to create MessageHistory from dict
        self.history = MessageHistory.model_validate(data)
        
        # Update internal tracking
        self.title = self.history.title
        self.scene_description = self.history.scene_description
        self.location = self.scene_description  # Maintain compatibility
        self.plot = self.scene_description
        
        return self.history