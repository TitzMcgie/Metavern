"""
Scene Manager for dynamic scene events that drive story forward.
Generates dramatic environmental events every time conversation stalls.
"""

from typing import List, Optional, Dict, Any
from config import Config
from data_models import Message, Scene
from openrouter_client import GenerativeModel
from helpers.response_parser import parse_json_response


class SceneManager:
    """Manages dynamic scene events that interrupt silence and push story forward."""
    
    def __init__(self, model_name: str = None):
        """
        Initialize the Scene Manager.
        """
        self.model_name = model_name or Config.DEFAULT_MODEL
        self.model = GenerativeModel(self.model_name)
        self.current_scene: Optional[Scene] = None
    
    def create_scene(
        self,
        location: str,
        initial_description: str
    ) -> Scene:
        """
        Create a new scene with initial description as first event.
        
        Args:
            location: Where this scene takes place
            initial_description: Opening scene description (becomes first event)
            
        Returns:
            New Scene instance
        """
        self.current_scene = Scene(
            location=location,
            recent_events=[initial_description],  
            conversation_context=[]
        )
        return self.current_scene
    
    def update_conversation_context(self, recent_messages: List[Message], max_context: int = 5):
        """
        Update scene's conversation context from recent messages.
        
        Args:
            recent_messages: Recent conversation messages
            max_context: Maximum number of topics to track
        """
        if not self.current_scene:
            return
        
        # Extract topics from recent messages
        topics = []
        for msg in recent_messages[-max_context:]:
            # Simple topic extraction - can be enhanced
            topics.append(f"{msg.speaker}: {msg.content[:50]}")
        
        self.current_scene.conversation_context = topics
    
    def generate_scene_event(
        self,
        recent_messages: List[Message],
        characters_present: List[str]
    ) -> str:
        """
        Generate a dramatic scene event when conversation stalls.
        Called EVERY time there's a silence round.
        
        Args:
            recent_messages: Recent conversation to understand context
            characters_present: Names of characters in the scene
            
        Returns:
            Description of the dramatic event
        """
        if not self.current_scene:
            return "The room remains quiet."
        
        try:
            # Update conversation context
            self.update_conversation_context(recent_messages)
            
            # Build context for event generation
            conversation_summary = ""
            if self.current_scene.conversation_context:
                conversation_summary = "\n".join(self.current_scene.conversation_context)
            
            # Build history to avoid repetition (skip first event which is initial description)
            recent_events_str = ""
            if len(self.current_scene.recent_events) > 1:
                # Skip the first event (initial description) when showing previous events
                events_to_show = self.current_scene.recent_events[1:-1][-3:]  # Last 3 events, excluding initial description
                if events_to_show:
                    recent_events_str = "\n\nPREVIOUS EVENTS (DO NOT REPEAT):\n" + "\n".join([f"- {event}" for event in events_to_show])
            
            prompt = f"""You are generating a DRAMATIC SCENE EVENT for a Harry Potter roleplay story.

CURRENT SCENE:
- Location: {self.current_scene.location}
- Initial Setting: {self.current_scene.recent_events[0]}
- Characters Present: {', '.join(characters_present)}
- Events Triggered So Far: {len(self.current_scene.recent_events) - 1}

RECENT CONVERSATION:
{conversation_summary}{recent_events_str}

SITUATION:
The conversation has stalled. Silence has fallen. You need to generate a DRAMATIC ENVIRONMENTAL EVENT that:

1. **Interrupts the silence** with something happening in the environment
2. **Demands character attention** - they MUST notice and react
3. **Pushes story forward** - reveals clues, creates new tension, or advances plot
4. **Is completely different** from previous events above

EVENT TYPES (choose dynamically):
- **Physical**: Wind blows, object falls, door slams, temperature changes
- **Discovery**: Hidden object revealed, clue appears, book falls open
- **Mysterious**: Strange sound, shadow moves, magic activates
- **Danger**: Warning sign, threat appears, protective spell triggers
- **Character**: Someone enters, portrait speaks, ghost appears

CRITICAL RULES:
- Make it SPECIFIC and VIVID (not generic)
- Include sensory details (what they see/hear/feel)
- Event should naturally lead to new conversation
- Must be something characters can react to
- Vary the type of event - don't repeat patterns

OUTPUT FORMAT (strict JSON):
{{
  "event_description": "2-3 sentence vivid description of what happens",
  "character_awareness": "What characters notice/feel about this event"
}}

EXAMPLE:
{{
  "event_description": "A sudden gust of ice-cold wind tears through the library, extinguishing half the torches. Pages flutter wildly as a single ancient book slides off a high shelf and crashes open on the table between them—landing on a page marked with a glowing symbol.",
  "character_awareness": "Both freeze. The symbol on the page is identical to the one from Ron's failed spell."
}}"""
            
            response = self.model.generate_content(prompt, temperature=0.85)
            result = parse_json_response(response.text)
            
            event_desc = result.get("event_description", "").strip()
            awareness = result.get("character_awareness", "").strip()
            
            # Combine description and awareness
            full_event = f"{event_desc}\n\n{awareness}" if awareness else event_desc
            
            # Track this event
            self.current_scene.recent_events.append(event_desc)
            
            # Keep initial description + last 5 events (total 6 items max)
            # First event (index 0) is always the initial scene description
            if len(self.current_scene.recent_events) > 6:
                # Remove oldest event but keep initial description
                self.current_scene.recent_events.pop(1)
            
            return full_event
            
        except Exception as e:
            # Fallback event
            return self._generate_fallback_event()
    
    def _generate_fallback_event(self) -> str:
        """Generate a simple fallback event if AI fails."""
        import random
        fallback_events = [
            "A sudden draft causes the fire to flare up, casting dramatic shadows across the walls. Everyone looks up instinctively.",
            "A distant sound echoes through the castle—something heavy falling. The room feels suddenly tense.",
            "One of the portraits on the wall clears its throat loudly, clearly trying to get everyone's attention.",
            "A book falls from a nearby shelf with a loud thud, landing open to a marked page.",
            "The torches flicker strangely, and for a moment, the shadows seem to move independently."
        ]
        return random.choice(fallback_events)
