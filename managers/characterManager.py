from typing import List, Optional, Dict, Any, Tuple
import sys
from pathlib import Path
import json
import google.generativeai as genai

sys.path.insert(0, str(Path(__file__).parent.parent))

from data_models import CharacterPersona, Message, Character, CharacterMemory, CharacterState
from config import Config


class CharacterManager:
    """Manager for character-related operations."""
    
    def __init__(self):
        """Initialize CharacterManager."""
        self.models: Dict[str, Any] = {}  # Cache for generative models
    
    def create_character(
        self, 
        persona: CharacterPersona, 
        memory: Optional[CharacterMemory] = None,
        state: Optional[CharacterState] = None
    ) -> Character:
        """
        Create a new AI character instance.
        
        Args:
            persona: CharacterPersona defining the character
            memory: Optional character memory
            state: Optional character state
            
        Returns:
            New Character instance
        """
        if memory is None:
            memory = CharacterMemory(character_name=persona.name)
        if state is None:
            state = CharacterState(character_name=persona.name)
        
        return Character(persona=persona, memory=memory, state=state)
    
    def create_multiple_characters(
        self,
        personas: List[CharacterPersona]
    ) -> List[Character]:
        """
        Create multiple AI characters at once.
        
        Args:
            personas: List of CharacterPersona objects
            
        Returns:
            List of Character instances
        """
        return [self.create_character(persona) for persona in personas]
    
    def get_character_by_name(self, characters: List[Character], name: str) -> Optional[Character]:
        """
        Find a character by name.
        
        Args:
            characters: List of Character instances
            name: Name to search for
            
        Returns:
            Character if found, None otherwise
        """
        for character in characters:
            if character.persona.name == name:
                return character
        return None
    
    def get_all_character_names(self, characters: List[Character]) -> List[str]:
        """Get list of all character names."""
        return [char.persona.name for char in characters]
    
    def update_character_mood(self, character: Character, mood: str) -> None:
        """Update character's mood."""
        if character.state:
            character.state.mood = mood
    
    def update_character_focus(self, character: Character, focus: str) -> None:
        """Update what the character is focusing on."""
        if character.state:
            character.state.focus = focus
    
    def add_observation(self, character: Character, observation: str) -> None:
        """Add an observation to character's memory."""
        if character.memory:
            character.memory.observations.append(observation)
    
    def add_perception(self, character: Character, perception: str) -> None:
        """Add a perception to character's memory."""
        if character.memory:
            character.memory.perceptions.append(perception)
    
    def get_or_create_model(self, model_name: str = None) -> Any:
        """Get or create a generative model."""
        model_name = model_name or Config.DEFAULT_MODEL
        if model_name not in self.models:
            self.models[model_name] = genai.GenerativeModel(model_name)
        return self.models[model_name]
    
    def build_persona_context(self, character: Character) -> str:
        """Build the character's personality context."""
        relationships_str = "\n".join([
            f"- {char}: {rel}" 
            for char, rel in character.persona.relationships.items()
        ])
        
        context = f"""You are {character.persona.name} in a roleplay conversation.

YOUR PERSONALITY:
- Traits: {', '.join(character.persona.traits)}
- Speaking Style: {character.persona.speaking_style}
- Background: {character.persona.background}

YOUR RELATIONSHIPS:
{relationships_str}"""
        
        # Add current state if available
        if character.state:
            context += f"\n\nYOUR CURRENT STATE:\n- Mood: {character.state.mood}"
            if character.state.focus:
                context += f"\n- Focus: {character.state.focus}"
            if character.state.current_action:
                context += f"\n- Current Action: {character.state.current_action}"
        
        return context
    
    def build_conversation_context(self, messages: List[Message]) -> str:
        """Build the conversation context string with actions noted."""
        context_lines = []
        for msg in messages:
            # Message content now includes action descriptions in format: *action* dialogue
            context_lines.append(f"{msg.speaker}: {msg.content}")
        return "\n".join(context_lines)
    
    def build_decision_prompt(
        self, 
        character: Character,
        conversation_history: List[Message], 
        story_context: Optional[str] = None,
        last_n_messages: int = None
    ) -> str:
        """
        Build the prompt for deciding whether to speak.
        
        Args:
            character: The AICharacter making the decision
            conversation_history: Full conversation history
            story_context: Optional story context to guide the narrative
            last_n_messages: Number of recent messages to include (defaults to Config.DEFAULT_CONTEXT_WINDOW)
            
        Returns:
            The complete prompt string
        """
        # Get recent messages
        context_window = last_n_messages or Config.DEFAULT_CONTEXT_WINDOW
        recent_messages = (
            conversation_history[-context_window:] 
            if len(conversation_history) > context_window
            else conversation_history
        )
        
        persona_context = self.build_persona_context(character)
        conversation_context = self.build_conversation_context(recent_messages)
        
        # Add story context if provided
        story_section = ""
        if story_context:
            story_section = f"\n{story_context}\n"
        
        prompt = f"""{persona_context}
{story_section}
RECENT CONVERSATION:
{conversation_context}

DECISION TASK:
Based on the conversation above, decide if you should respond right now.

Consider:
1. Is the topic relevant to you or your interests?
2. Were you directly addressed or mentioned?
3. Would your input add VALUE and a NEW PERSPECTIVE to the conversation?
4. Is it natural timing (not interrupting, not creating awkward silence)?
5. Have you spoken too recently? (Don't dominate the conversation)
6. Would another character be better suited to respond first?
7. **CRITICAL**: If someone just said something similar to what you'd say, DON'T repeat it!
8. **CRITICAL**: Bring YOUR unique perspective based on YOUR personality, not echoing others!
9. **RESPECT BOUNDARIES**: If someone has clearly stated their position multiple times (2-3+), RESPECT IT. Don't keep pushing.
10. **INDEPENDENCE**: Don't just agree with or support what another character said. Have your OWN opinion.
11. **NATURAL CONVERSATION**: Sometimes the right response is to back off, change the subject, or accept what someone said.
12. **AVOID GANGING UP**: If another character is already pressing someone, don't pile on unless you have a DIFFERENT perspective.

CRITICAL RULES FOR NATURAL CONVERSATION:
- If someone says "I'm fine" or similar 2-3 times, BELIEVE THEM or drop it gracefully
- Don't make every conversation a confrontation or intervention
- Characters can disagree with each other, not just team up
- Sometimes the best response is acceptance: "Okay, if you say so" or changing the subject
- Not everything needs to be analyzed or probed deeply
- Respect when someone wants to end a topic

OUTPUT FORMAT (strict JSON):
{{
  "wants_to_speak": true or false,
  "priority": 0.0 to 1.0 (how urgent/important is your response),
  "reasoning": "brief explanation of your decision",
  "action_description": "brief narrative of your physical actions/body language (if any)",
  "message": "your actual dialogue if wants_to_speak is true, otherwise null"
}}

IMPORTANT:
- Include BOTH action descriptions AND dialogue to make it vivid and immersive
- Action description should show body language, gestures, facial expressions, movements

**CRITICAL - ACTION VARIETY RULES (READ THIS CAREFULLY):**
1. **CHECK THE CONVERSATION ABOVE** - Look at your previous messages. What actions did you ALREADY do?
2. **NEVER REPEAT ACTIONS** - If you already "leaned forward", "sat back", "crossed arms", "looked at someone" - DON'T DO IT AGAIN
3. **PHYSICAL CONSISTENCY** - If you already sat down or leaned back, you can't lean back AGAIN. Instead: stand up, walk somewhere, gesture differently, adjust position, look away, etc.
4. **VARIETY IS MANDATORY** - Each of your actions MUST be different from all your previous actions in this conversation
5. **EXAMPLES OF VARIETY**:
   - First message: "leans back against sofa"
   - Second message: "sits forward suddenly" or "stands up" or "runs hand through hair"
   - Third message: "paces to the window" or "fidgets with wand" or "slumps in chair"
   - NEVER: "leans back" again after already doing it!

- Be natural and conversational - you're a TEENAGER talking to your best friends
- Stay COMPLETELY IN CHARACTER with your unique speaking style
- Don't repeat what others just said - add something NEW or DON'T SPEAK
- Keep messages SHORT (1-3 sentences usually) and realistic for casual conversation
- If you have nothing unique to add, set wants_to_speak to false
- Your personality should be OBVIOUS from how you speak and act
- Don't sound like you're giving a lecture or writing an essay
- Use natural dialogue, contractions, and emotion
- Show, don't tell - use actions to convey mood and personality
- **INDEPENDENCE**: Have your own opinions - don't just support what others said
- **BACKING OFF**: Sometimes "Alright, fair enough" or "Suit yourself" is the perfect response
- **RESPECTING AUTONOMY**: If someone clearly doesn't want to talk about something, that's OKAY
- **NATURAL FLOW**: Not every topic needs resolution. Sometimes you just move on.
"""
        return prompt
    
    def parse_json_response(self, response_text: str) -> dict:
        """
        Parse JSON response, handling markdown code blocks.
        
        Args:
            response_text: Raw response text from the model
            
        Returns:
            Parsed JSON dictionary
        """
        response_text = response_text.strip()
        
        # Remove markdown code blocks
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        elif response_text.startswith("```"):
            response_text = response_text[3:]
        
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        response_text = response_text.strip()
        
        return json.loads(response_text)
    
    def decide_to_speak(
        self, 
        character: Character,
        conversation_history: List[Message],
        story_context: Optional[str] = None,
        model_name: str = None
    ) -> Tuple[bool, float, str, Optional[str], Optional[str]]:
        """
        Decide whether this character should speak.
        
        Args:
            character: The Character making the decision
            conversation_history: The full conversation history
            story_context: Optional story context to guide responses
            model_name: Optional model name override
            
        Returns:
            Tuple of (wants_to_speak, priority, reasoning, action_description, message)
        """
        try:
            prompt = self.build_decision_prompt(character, conversation_history, story_context)
            model = self.get_or_create_model(model_name)
            response = model.generate_content(prompt)
            
            # Parse JSON response
            decision_data = self.parse_json_response(response.text)
            
            return (
                decision_data.get("wants_to_speak", False),
                decision_data.get("priority", 0.0),
                decision_data.get("reasoning", "No reasoning provided"),
                decision_data.get("action_description", None),
                decision_data.get("message", None)
            )
            
        except Exception as e:
            # Return default non-speaking decision on error
            return (False, 0.0, f"Error in processing: {str(e)}", None, None)
    
    def add_spoken_message(self, character: Character, message: Message) -> None:
        """Add a message to character's spoken messages memory."""
        if character.memory and message.speaker == character.persona.name:
            character.memory.spoken_messages.append(message)
    
    def decide_to_speak_with_timing(
        self,
        character: Character,
        messages: List[Message],
        time_since_last_message: float,
        awkward_silence_threshold: float,
        story_context: Optional[str] = None,
        model_name: str = None
    ) -> Tuple[bool, float, str, Optional[str]]:
        """
        Decide whether character should speak, considering timing and emotional state.
        
        Args:
            character: The Character making the decision
            messages: Conversation history
            time_since_last_message: Seconds since last message
            awkward_silence_threshold: How many seconds before silence is awkward
            story_context: Optional story context
            model_name: Optional model name override
            
        Returns:
            Tuple of (wants_to_speak, priority, reasoning, message)
        """
        # If character is deliberately silent, don't speak
        if character.state and character.state.is_silent:
            return (False, 0.0, f"Staying silent because: {character.state.silence_reason}", None)
        
        # Build timing context
        timing_info = ""
        if time_since_last_message >= awkward_silence_threshold:
            timing_info = f"\n⚠️ AWKWARD SILENCE: It's been {time_since_last_message:.1f} seconds since anyone spoke. This is getting uncomfortable."
        
        # Check if someone was talking to this character specifically
        direct_address = False
        if messages:
            last_msg = messages[-1]
            if character.persona.name.lower() in last_msg.content.lower():
                direct_address = True
                timing_info += f"\n🎯 DIRECT ADDRESS: {last_msg.speaker} just said something to you specifically!"
        
        # Build enhanced prompt with timing
        persona_context = self.build_persona_context(character)
        conversation_context = self.build_conversation_context(messages[-15:] if len(messages) > 15 else messages)
        
        # Check what this character said recently
        recent_own_messages = [msg.content for msg in messages[-5:] if msg.speaker == character.persona.name]
        repetition_warning = ""
        if recent_own_messages:
            repetition_warning = f"""
⚠️ WARNING - DON'T REPEAT YOURSELF:
You recently said:
{chr(10).join(['- "' + msg + '"' for msg in recent_own_messages])}

If you're about to say something VERY similar, set wants_to_speak to FALSE!
Only speak if you have something NEW to add!
"""
        
        story_section = ""
        if story_context:
            story_section = f"\n{story_context}\n"
        
        # Add emotional state context
        emotional_context = ""
        if character.state:
            emotional_context = f"\nYOUR CURRENT EMOTIONAL STATE: {character.state.mood}"
            if character.state.focus:
                emotional_context += f"\nYOU'RE THINKING ABOUT: {character.state.focus}"
        
        prompt = f"""{persona_context}
{story_section}{emotional_context}
RECENT CONVERSATION (with REAL timestamps):
{conversation_context}
{repetition_warning}
TIMING CONTEXT:
- Seconds since last message: {time_since_last_message:.1f}
- Awkward silence threshold: {awkward_silence_threshold:.1f} seconds
{timing_info}

DECISION TASK:
Based on the conversation AND timing, decide if you should respond right now.

Consider:
1. **CRITICAL**: Have you ALREADY said this exact point? If YES → wants_to_speak = FALSE
2. Were you directly addressed? If YES, you SHOULD respond (unless deliberately staying silent)
3. Has there been an awkward silence? Someone should probably say something NEW
4. If someone asked YOU a question and you didn't answer, you might ask again or wonder why
5. Are you upset about something said? You might stay quiet, or speak up about it
6. Is the conversation flowing naturally, or do you have something UNIQUE to add?
7. Don't interrupt if someone just spoke seconds ago
8. Be NATURAL - but don't repeat yourself like a broken record

REPETITION RULE:
- If you've made your point 2+ times already → STAY QUIET or change the subject
- Don't keep asking the same question if they already answered "I don't know"
- If they clearly don't know something, accept it and move on or suggest something else

EMOTIONAL REACTIONS (stay in character!):
- If someone was rude to you: You might get hurt, angry, or silent
- If someone told you to shut up: You might feel hurt and stop talking
- If your friend ignores your question: You might ask again or call them out
- If there's awkward silence: You might make a joke, ask if everyone's okay, or bring up something new

OUTPUT FORMAT (strict JSON):
{{
  "wants_to_speak": true or false,
  "priority": 0.0 to 1.0 (higher if directly addressed or awkward silence),
  "reasoning": "brief explanation including emotional state if relevant",
  "message": "your actual dialogue if wants_to_speak is true, otherwise null"
}}

CRITICAL:
- Be a REAL TEENAGER with REAL EMOTIONS - not a robot
- If someone was mean, REACT emotionally
- If there's silence and you were asked something, you might ask again
- Keep it SHORT and natural (1-3 sentences)
- Show personality in EVERY message
"""
        
        try:
            model = self.get_or_create_model(model_name)
            response = model.generate_content(prompt)
            decision_data = self.parse_json_response(response.text)
            
            # Boost priority if direct address or awkward silence
            priority = decision_data.get("priority", 0.0)
            if direct_address:
                priority = min(1.0, priority + 0.3)
            if time_since_last_message >= awkward_silence_threshold:
                priority = min(1.0, priority + 0.2)
            
            return (
                decision_data.get("wants_to_speak", False),
                priority,
                decision_data.get("reasoning", "No reasoning provided"),
                decision_data.get("message", None)
            )
            
        except Exception as e:
            return (False, 0.0, f"Error: {str(e)}", None)