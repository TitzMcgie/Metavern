"""
Narrator Manager for autonomous scene transitions and environmental storytelling.
Handles time progression, environmental changes, and narrative events.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from config import Config
from data_models import Message
from openrouter_client import GenerativeModel


class NarratorManager:
    """Manages narrative transitions, time progression, and environmental storytelling."""
    
    def __init__(self, model_name: str = None):
        """
        Initialize the Narrator Manager.
        
        Args:
            model_name: Gemini model to use (defaults to Config.DEFAULT_MODEL)
        """
        self.model_name = model_name or Config.DEFAULT_MODEL
        self.model = None
        self.current_time_of_day = "evening"  # evening, night, late_night, dawn, morning, afternoon
        self.environment_state = {
            "fire": "crackling warmly",
            "lighting": "warm and golden",
            "temperature": "comfortable",
            "sounds": ["fire crackling", "wind outside"],
            "time_passed_hours": 0
        }
        
    def get_or_create_model(self) -> Any:
        """Get or create the generative model."""
        if self.model is None:
            self.model = GenerativeModel(self.model_name)
        return self.model
    
    def advance_time(self, hours: float = 1.0) -> str:
        """
        Advance time and update environment accordingly.
        
        Args:
            hours: Number of hours to advance
            
        Returns:
            Description of time change
        """
        self.environment_state["time_passed_hours"] += hours
        
        # Update time of day
        if self.current_time_of_day == "evening" and hours >= 2:
            self.current_time_of_day = "night"
            return "evening → night"
        elif self.current_time_of_day == "night" and hours >= 3:
            self.current_time_of_day = "late_night"
            return "night → late night"
        elif self.current_time_of_day == "late_night" and hours >= 2:
            self.current_time_of_day = "dawn"
            return "late night → dawn"
        elif self.current_time_of_day == "dawn" and hours >= 1:
            self.current_time_of_day = "morning"
            return "dawn → morning"
        
        return f"time passes ({hours} hours)"
    
    def update_environment_for_time(self):
        """Update environmental details based on current time."""
        if self.current_time_of_day == "evening":
            self.environment_state.update({
                "fire": "crackling warmly",
                "lighting": "warm and golden from firelight",
                "sounds": ["fire crackling", "distant voices", "wind outside"]
            })
        elif self.current_time_of_day == "night":
            self.environment_state.update({
                "fire": "burning steadily, flames dancing",
                "lighting": "dimmer, shadows lengthening",
                "sounds": ["fire popping", "wind howling outside", "building settling"]
            })
        elif self.current_time_of_day == "late_night":
            self.environment_state.update({
                "fire": "dying down to embers, glowing faintly",
                "lighting": "very dim, mostly darkness",
                "sounds": ["embers crackling softly", "silence", "distant owl hooting"]
            })
        elif self.current_time_of_day == "dawn":
            self.environment_state.update({
                "fire": "reduced to ashes with faint wisps of smoke",
                "lighting": "pale grey light filtering through windows",
                "sounds": ["birds chirping faintly", "castle waking up", "footsteps in distance"]
            })
        elif self.current_time_of_day == "morning":
            self.environment_state.update({
                "fire": "cold ashes in the hearth",
                "lighting": "bright morning sunlight streaming through windows",
                "sounds": ["students chattering", "footsteps", "breakfast smells wafting up"]
            })
    
    def detect_conversation_stagnation(
        self,
        silence_rounds: int,
        recent_messages: List[Message],
        player_name: str
    ) -> bool:
        """
        Detect if conversation has stagnated and needs narrative intervention.
        
        Args:
            silence_rounds: Number of consecutive rounds with no speakers
            recent_messages: Recent conversation messages
            player_name: Name of the player character
            
        Returns:
            True if narrator should intervene
        """
        # Intervene after 2 rounds of silence
        if silence_rounds >= 2:
            return True
        
        # Also check if player has been absent for multiple rounds
        if recent_messages:
            last_speakers = [msg.speaker for msg in recent_messages[-5:]]
            if player_name not in last_speakers and silence_rounds >= 1:
                return True
        
        return False
    
    def generate_transition_narrative(
        self,
        current_scene: str,
        recent_messages: List[Message],
        silence_rounds: int,
        player_name: str
    ) -> str:
        """
        Generate a narrative transition to move the story forward.
        
        Args:
            current_scene: Current scene description
            recent_messages: Recent conversation messages
            silence_rounds: How many silent rounds
            player_name: Name of the player character
            
        Returns:
            Narrative transition text
        """
        try:
            # Update environment based on time
            time_change = self.advance_time(hours=2.0 if silence_rounds >= 2 else 1.0)
            self.update_environment_for_time()
            
            # Build context from recent conversation
            conversation_summary = ""
            if recent_messages:
                last_few = recent_messages[-3:]
                conversation_summary = "\n".join([f"{msg.speaker}: {msg.content[:100]}" for msg in last_few])
            
            # Check if player is absent (based on action_description set by withdrawal detector)
            player_absent = False
            if recent_messages:
                last_msg = recent_messages[-1]
                # Check if the last message was from player with a leaving action
                if last_msg.speaker == player_name and last_msg.action_description:
                    # Player has an action description - could be leaving
                    # We rely on the withdrawal detector to have properly detected this
                    player_absent = True
            
            prompt = f"""You are a narrator for an interactive Harry Potter roleplay story.

CURRENT SITUATION:
- Time of day: {self.current_time_of_day}
- Fire state: {self.environment_state['fire']}
- Lighting: {self.environment_state['lighting']}
- Location: Gryffindor Common Room
- Player ({player_name}) status: {"sleeping/resting" if player_absent else "present"}

RECENT CONVERSATION:
{conversation_summary}

CONTEXT:
The conversation has gone quiet. {silence_rounds} rounds of silence have passed.
Time has advanced: {time_change}

TASK:
Write a brief, atmospheric narrative transition (2-4 sentences) that:
1. Describes how time has passed (environmental changes)
2. Shows the passage of time through details (fire dying, light changing, etc.)
3. Creates a natural bridge to the next scene
4. If it's morning now, describe someone waking up or the new day beginning
5. If player is sleeping, you can describe them sleeping and others retiring/waking

STYLE:
- Vivid, sensory details (sight, sound, touch)
- Atmospheric and immersive
- Brief but evocative
- Harry Potter universe tone
- Present tense

OUTPUT:
Just the narrative text, no quotes or labels. Write as the narrator.
"""
            
            model = self.get_or_create_model()
            response = model.generate_content(prompt)
            
            return response.text.strip()
            
        except Exception as e:
            # Fallback to template-based transition
            return self._generate_fallback_transition(player_absent)
    
    def _generate_fallback_transition(self, player_sleeping: bool = False) -> str:
        """Generate a simple fallback transition if AI fails."""
        transitions = {
            "evening": "The evening deepens. The fire crackles lower, casting dancing shadows on the walls. The common room grows quieter as more students head to bed.",
            "night": "Hours pass. The fire burns down to glowing embers, its light dimming. The common room is silent now, save for the occasional pop of a coal and the wind outside.",
            "late_night": "The night wears on. The fire has nearly died, leaving only faint embers. Darkness fills the room, broken only by pale moonlight through the windows.",
            "dawn": "Dawn breaks. Grey light filters through the tall windows as the first birds begin to chirp. The fire is cold ashes now. A new day is beginning.",
            "morning": "Morning arrives in full. Bright sunlight streams through the windows, warming the room. The sounds of the castle waking up echo through the halls."
        }
        
        transition = transitions.get(self.current_time_of_day, transitions["evening"])
        
        if player_sleeping and self.current_time_of_day == "morning":
            transition += " It's time to wake up."
        
        return transition
    
    def generate_wakeup_event(
        self,
        player_name: str,
        other_characters: List[str]
    ) -> Optional[str]:
        """
        Generate a wakeup event when it's time to resume the story.
        
        Args:
            player_name: Name of sleeping player
            other_characters: Names of other characters present
            
        Returns:
            Description of wakeup event, or None
        """
        if self.current_time_of_day not in ["dawn", "morning"]:
            return None
        
        try:
            prompt = f"""You are narrating a Harry Potter story. {player_name} fell asleep in the common room last night. 
It's now {self.current_time_of_day}. 

Write a brief (1-2 sentences) description of {player_name} waking up naturally or being woken by one of their friends ({', '.join(other_characters)}).

Be specific about WHO wakes them and HOW (gentle shake, calling their name, etc.).
Write in present tense, vivid and atmospheric.
Just the narrative description, no character dialogue."""
            
            model = self.get_or_create_model()
            response = model.generate_content(prompt)
            
            return response.text.strip()
            
        except Exception as e:
            # Fallback
            if other_characters:
                return f"Morning light wakes {player_name}. {other_characters[0]} is already awake, watching with concern."
            return f"{player_name} stirs awake as morning sunlight streams through the windows."
    
    def should_trigger_wakeup(self) -> bool:
        """Check if it's time to trigger a wakeup event."""
        return self.current_time_of_day in ["dawn", "morning"]
    
    def reset_time(self, time_of_day: str = "evening"):
        """Reset time to a specific point."""
        self.current_time_of_day = time_of_day
        self.environment_state["time_passed_hours"] = 0
        self.update_environment_for_time()
