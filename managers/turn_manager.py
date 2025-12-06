"""
Turn management system for natural conversation flow.
Handles ONLY turn decision logic - determines who should speak next.
All message operations are delegated to MessageManager.
"""

import random
import time
from typing import List, Optional, Tuple

from data_models import Message, MessageHistory, Character
from managers.messageManager import MessageManager
from managers.sceneManager import SceneManager
from managers.characterManager import CharacterManager
from managers.storyManager import StoryManager
from config import Config


class TurnManager:
    """
    Manages conversation flow and turn selection with natural timing.
    
    Responsibilities:
    - Decide who should speak next based on context
    - Coordinate between AI characters to determine speaking order
    - Process consecutive AI responses naturally
    """
    
    def __init__(
        self,
        characters: List[Character],
        player_name: str,
        story_manager: Optional[StoryManager] = None,
        max_consecutive_ai_turns: int = None,
        priority_randomness: float = None
    ):
        """
        Initialize the turn manager.
        
        Args:
            characters: List of AI characters in the conversation
            player_name: Name of the human player
            story_manager: Optional story manager for narrative progression
            max_consecutive_ai_turns: Maximum number of consecutive AI turns (defaults to Config.MAX_CONSECUTIVE_AI_TURNS)
            priority_randomness: Random factor to add to priority for naturalness (defaults to Config.PRIORITY_RANDOMNESS)
        """
        self.characters = characters
        self.player_name = player_name
        self.story_manager = story_manager
        self.max_consecutive_ai_turns = max_consecutive_ai_turns or Config.MAX_CONSECUTIVE_AI_TURNS
        self.priority_randomness = priority_randomness or Config.PRIORITY_RANDOMNESS
        
        # Initialize managers
        self.message_manager = MessageManager()
        self.scene_manager = SceneManager()
        self.character_manager = CharacterManager()
        
        # Initialize scene with all participants
        all_participants = [player_name] + [char.persona.name for char in characters]
        self.scene = self.scene_manager.create_scene(
            participants=all_participants
        )
        
        self.turn_count = 0
    
    def _collect_speaking_decisions(self) -> List[Tuple[Character, Tuple[bool, float, str, Optional[str]]]]:
        """
        Collect speaking decisions from all AI characters.
        
        Returns:
            List of tuples containing (character, decision_tuple) for characters that want to speak
        """
        decisions = []
        
        # Get story context if available
        story_context = None
        if self.story_manager:
            story_context = self.story_manager.get_story_context()
        
        for character in self.characters:
            wants_to_speak, priority, reasoning, action_desc, message = self.character_manager.decide_to_speak(
                character,
                self.scene.messages,
                story_context=story_context
            )
            
            if wants_to_speak:
                decisions.append((character, (wants_to_speak, priority, reasoning, action_desc, message)))
                print(f"   💭 {character.persona.name}: "
                      f"Priority {priority:.2f} - {reasoning}")
        
        return decisions
    
    def _select_speaker_from_decisions(
        self, 
        decisions: List[Tuple[Character, Tuple[bool, float, str, Optional[str], Optional[str]]]]
    ) -> Optional[Tuple[Character, Optional[str], str]]:
        """
        Select which character should speak based on priorities.
        
        Args:
            decisions: List of (character, decision_tuple) tuples
            
        Returns:
            Tuple of (character, action_description, message) or None if no valid speakers
        """
        if not decisions:
            return None
        
        # Sort by priority with small random factor for naturalness
        decisions_with_adjusted_priority = [
            (char, decision_tuple, decision_tuple[1] + random.uniform(-self.priority_randomness, self.priority_randomness))
            for char, decision_tuple in decisions
        ]
        
        decisions_with_adjusted_priority.sort(key=lambda x: x[2], reverse=True)
        
        # Return the highest priority character with their action and message
        selected_character, decision_tuple, _ = decisions_with_adjusted_priority[0]
        action_desc = decision_tuple[3]  # Extract action description
        message = decision_tuple[4]  # Extract message from tuple
        return (selected_character, action_desc, message)
    
    def select_next_speaker(self) -> Optional[Tuple[Character, Optional[str], str]]:
        """
        Select which AI character should speak next.
        
        Returns:
            Tuple of (character, action_description, message) for the selected speaker, or None
        """
        if not self.scene.messages:
            return None
        
        print("\n🤔 AI characters are thinking...")
        
        # Collect decisions from all characters
        decisions = self._collect_speaking_decisions()
        
        if not decisions:
            print("   💤 No one wants to speak right now.")
            return None
        
        # Select the speaker
        result = self._select_speaker_from_decisions(decisions)
        
        return result
    
    def process_ai_responses(self, max_turns: Optional[int] = None) -> List[Tuple[Character, str]]:
        """
        Process AI responses ONE AT A TIME until no one wants to speak or max turns reached.
        Each character sees the updated conversation including previous AI responses.
        Returns the list of (character, message) tuples for the caller to handle.
        
        Args:
            max_turns: Maximum number of consecutive AI turns (uses default if None)
            
        Returns:
            List of (character, message) tuples for AI turns that want to speak
        """
        if max_turns is None:
            max_turns = self.max_consecutive_ai_turns
        
        responses = []
        consecutive_count = 0
        last_speaker = None
        
        while consecutive_count < max_turns:
            # Check for story events ONLY after multiple AI turns (not immediately)
            # And only when conversation is flowing naturally, not at transition points
            if self.story_manager and consecutive_count >= 2:
                message_count = len(self.scene.messages)
                event = self.story_manager.check_for_story_event(
                    silence_duration=consecutive_count,
                    message_count=message_count,
                    recent_messages=self.scene.messages[-3:] if len(self.scene.messages) >= 3 else self.scene.messages
                )
                if event:
                    self.story_manager.display_story_event(event)
                    # Add event as a narrative message
                    event_msg = self.message_manager.create_message(
                        speaker="Narrator",
                        content=f"[{event['title']}] {event['description']}"
                    )
                    self.message_manager.add_message(self.scene, event_msg)
                    # Events interrupt the AI conversation flow
                    break
            
            print("\n🤔 AI characters are thinking...")
            
            # Ask ONE character at a time (sequentially, not in parallel)
            result = self.select_next_speaker()
            
            if result is None:
                break
            
            character, action_desc, message = result
            
            # Prevent the same character from speaking twice in a row
            if last_speaker == character.persona.name:
                print(f"   ⏭️  {character.persona.name} already spoke, giving others a chance...")
                break
            
            responses.append((character, message))
            
            # CRITICAL: Add the message to the scene immediately so the next character sees it
            # Include action description in content so AI can see previous actions
            full_content = f"*{action_desc}* {message}" if action_desc else message
            message_obj = self.message_manager.create_message(
                speaker=character.persona.name,
                content=full_content
            )
            self.message_manager.add_message(self.scene, message_obj)
            
            # Print with action description if available
            print(f"\n💬 {character.persona.name}:", end="")
            if action_desc:
                print(f" *{action_desc}*")
                print(f"   \"{message}\"")
            else:
                print(f" {message}")
            
            last_speaker = character.persona.name
            consecutive_count += 1
            
            # Small delay for readability and to let next character see the context
            time.sleep(2)
        
        return responses