"""
Manager for story progression and narrative flow with sequential objective system.
"""

from typing import Optional, List, Dict, Any
import sys
from pathlib import Path
import json
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_models import Story, Character, TimelineEvent
from config import Config
from openrouter_client import GenerativeModel


class StoryManager:
    """Manager for sequential story objectives and character objective assignment."""
    
    def __init__(self, story: Optional[Story] = None):
        """
        Initialize StoryManager.
        
        Args:
            story: The story to manage
        """
        self.story = story
        self.model = GenerativeModel(Config.DEFAULT_MODEL)
    
    def set_story_arc(self, story: Story) -> None:
        """Set the story arc."""
        self.story = story
    
    def get_current_objective(self) -> Optional[str]:
        """Get the current story objective."""
        if self.story and self.story.current_objective_index < len(self.story.objectives):
            return self.story.objectives[self.story.current_objective_index]
        return None
    
    def is_story_complete(self) -> bool:
        """Check if all story objectives are complete."""
        if not self.story:
            return True
        return self.story.current_objective_index >= len(self.story.objectives)
    
    def get_progress_percentage(self) -> float:
        """Get the percentage of story completion."""
        if not self.story or len(self.story.objectives) == 0:
            return 100.0
        return (self.story.current_objective_index / len(self.story.objectives)) * 100
    
    def get_story_context(self) -> str:
        """Get the current story context for AI characters."""
        if not self.story:
            return "No story defined."
        
        current_objective = self.get_current_objective()
        if not current_objective:
            return "Story completed! All objectives achieved."
        
        progress = self.get_progress_percentage()
        
        context = f"""
STORY: {self.story.title}
Progress: {progress:.0f}% ({self.story.current_objective_index + 1} of {len(self.story.objectives)} objectives)

CURRENT STORY OBJECTIVE:
{current_objective}

OVERALL STORY CONTEXT:
{self.story.description}

Remember: Work naturally toward accomplishing the current objective through your character's unique perspective and abilities.
"""
        return context
    
    def assign_initial_objectives(
        self,
        active_characters: List[Character],
        timeline_context: str
    ) -> Dict[str, str]:
        """
        Assign initial character objectives at story start or when objective advances.
        
        Args:
            active_characters: List of currently active characters
            timeline_context: Recent timeline context
            
        Returns:
            Dictionary mapping character names to their new objectives
        """
        if not self.story or self.is_story_complete():
            return {char.persona.name: None for char in active_characters}
        
        current_objective = self.get_current_objective()
        
        # Build character descriptions
        char_descriptions = []
        for char in active_characters:
            traits = ", ".join(char.persona.traits)
            char_descriptions.append(
                f"- {char.persona.name}: {traits}. Speaking style: {char.persona.speaking_style}"
            )
        
        prompt = f"""You are assigning objectives to characters in an interactive roleplay story.

STORY: {self.story.title}
{self.story.description}

CURRENT STORY OBJECTIVE (what needs to be achieved):
{current_objective}

ACTIVE CHARACTERS:
{chr(10).join(char_descriptions)}

RECENT CONTEXT:
{timeline_context}

TASK: Assign ONE specific objective to EACH character that helps achieve the current story objective.

Guidelines:
- Make objectives specific enough to guide the character, but flexible enough to allow creativity
- Consider each character's unique abilities and personality
- Objectives should be complementary (characters working together from different angles)
- Objectives should be achievable through conversation/action in 3-10 turns
- Don't assign the exact same objective to multiple characters

Respond ONLY with valid JSON in this format:
{{
  "character_objectives": {{
    "CharacterName1": "specific objective for this character",
    "CharacterName2": "specific objective for this character"
  }}
}}"""

        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Extract JSON from response
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(response_text)
            return result.get("character_objectives", {})
            
        except Exception as e:
            print(f"⚠️ Error assigning initial objectives: {e}")
            # Fallback: generic objectives
            return {
                char.persona.name: f"Help achieve: {current_objective}"
                for char in active_characters
            }
    
    def evaluate_progress(
        self,
        active_characters: List[Character],
        recent_timeline_events: List[TimelineEvent]
    ) -> Dict[str, Any]:
        """
        Judge LLM evaluates character objective completion and story objective completion.
        
        Args:
            active_characters: List of currently active characters
            recent_timeline_events: Recent timeline events for context
            
        Returns:
            Dictionary with evaluation results:
            {
                "character_evaluations": {
                    "CharacterName": {"completed": bool, "new_objective": str or None}
                },
                "story_objective_complete": bool,
                "reasoning": str
            }
        """
        if not self.story or self.is_story_complete():
            return {
                "character_evaluations": {},
                "story_objective_complete": True,
                "reasoning": "Story is complete"
            }
        
        current_story_objective = self.get_current_objective()
        
        # Build timeline summary
        timeline_summary = []
        for event in recent_timeline_events[-15:]:  # Last 15 events
            if hasattr(event, 'character') and hasattr(event, 'dialouge'):
                # Message
                timeline_summary.append(f"{event.character}: {event.dialouge}")
            elif hasattr(event, 'character') and hasattr(event, 'description') and hasattr(event, '__class__'):
                # Action, Scene, Entry, Exit
                event_type = event.__class__.__name__
                if event_type == "Action":
                    timeline_summary.append(f"[ACTION] {event.character}: {event.description}")
                elif event_type == "CharacterEntry":
                    timeline_summary.append(f"[ENTRY] {event.character} entered: {event.description}")
                elif event_type == "CharacterExit":
                    timeline_summary.append(f"[EXIT] {event.character} left: {event.description}")
                elif event_type == "Scene":
                    timeline_summary.append(f"[SCENE at {event.location}]: {event.description}")
        
        timeline_text = "\n".join(timeline_summary) if timeline_summary else "No recent events"
        
        # Build character objectives summary
        char_objectives = []
        for char in active_characters:
            if char.state and char.state.current_objective:
                char_objectives.append(f"- {char.persona.name}: \"{char.state.current_objective}\"")
            else:
                char_objectives.append(f"- {char.persona.name}: No objective assigned")
        
        char_objectives_text = "\n".join(char_objectives)
        
        prompt = f"""You are evaluating story progression in an interactive roleplay.

CURRENT STORY OBJECTIVE (Overall goal to achieve):
{current_story_objective}

ACTIVE CHARACTERS AND THEIR CURRENT OBJECTIVES:
{char_objectives_text}

RECENT CONVERSATION (Last 15 events):
{timeline_text}

EVALUATE:

1. For EACH character - has their current objective been completed based on recent conversation?
   - Consider: Did they accomplish what was asked, even if indirectly?
   - Consider: Has enough progress been made to mark it complete?
   - If YES and story is continuing, provide a NEW objective for them
   - If NO, they keep their current objective

2. For the STORY OBJECTIVE - has it been achieved?
   - Consider: Has the conversation naturally accomplished the story goal?
   - Consider: Even if not all character objectives are done, is the story goal met?
   - Consider: Has the purpose of this objective been fulfilled?

Respond ONLY with valid JSON in this format:
{{
  "character_evaluations": {{
    "CharacterName1": {{
      "completed": true/false,
      "new_objective": "new objective string if completed=true AND story continuing, otherwise null",
      "reasoning": "brief explanation"
    }}
  }},
  "story_objective_complete": true/false,
  "reasoning": "explain why story objective is or isn't complete"
}}"""

        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Extract JSON from response
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(response_text)
            return result
            
        except Exception as e:
            print(f"⚠️ Error in judge evaluation: {e}")
            # Fallback: no changes
            return {
                "character_evaluations": {
                    char.persona.name: {
                        "completed": False,
                        "new_objective": None,
                        "reasoning": "Evaluation error"
                    }
                    for char in active_characters
                },
                "story_objective_complete": False,
                "reasoning": f"Error during evaluation: {e}"
            }
    
    def advance_story_objective(self) -> bool:
        """
        Advance to the next story objective.
        
        Returns:
            True if advanced successfully, False if story is complete
        """
        if not self.story:
            return False
        
        if self.story.current_objective_index < len(self.story.objectives) - 1:
            self.story.current_objective_index += 1
            return True
        else:
            # Story complete
            self.story.current_objective_index = len(self.story.objectives)
            return False
    
    def get_progress_summary(self) -> str:
        """Get a summary of story progress."""
        if not self.story:
            return "No story active."
        
        if self.is_story_complete():
            return f"""
📖 Story Complete: {self.story.title}
✅ All {len(self.story.objectives)} objectives achieved!
"""
        
        current_objective = self.get_current_objective()
        progress = self.get_progress_percentage()
        
        return f"""
📖 Story: {self.story.title}
📊 Progress: {progress:.0f}% 
🎯 Objective {self.story.current_objective_index + 1} of {len(self.story.objectives)}
   "{current_objective}"
"""