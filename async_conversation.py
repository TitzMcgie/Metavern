"""
Asynchronous conversation system that allows natural, interruptible conversation.
Characters can be interrupted, respond to silence, and react emotionally in real-time.
"""

import threading
import time
from datetime import datetime
from typing import List, Optional
from queue import Queue

from data_models import Character, Message, Scene
from managers.characterManager import CharacterManager
from managers.messageManager import MessageManager
from managers.sceneManager import SceneManager
from managers.storyManager import StoryManager


class AsyncConversationManager:
    """
    Manages real-time, asynchronous conversation where:
    - Player can interrupt at any time
    - AI characters think in background and speak when ready
    - Characters react to silence naturally (asking again, getting impatient)
    - Characters can stay silent if upset or told to be quiet
    - Timestamps matter - awkward silences are detected
    """
    
    def __init__(
        self,
        characters: List[Character],
        player_name: str,
        scene_manager: SceneManager,
        story_manager: Optional[StoryManager] = None,
        awkward_silence_threshold: float = 10.0  # seconds
    ):
        """
        Initialize async conversation manager.
        
        Args:
            characters: List of AI characters
            player_name: Name of human player
            scene_manager: Scene manager instance
            story_manager: Optional story manager
            awkward_silence_threshold: How many seconds of silence triggers AI reactions
        """
        self.characters = characters
        self.player_name = player_name
        self.scene_manager = scene_manager
        self.story_manager = story_manager
        self.awkward_silence_threshold = awkward_silence_threshold
        
        # Initialize managers
        self.character_manager = CharacterManager()
        self.message_manager = MessageManager()
        
        # Conversation state
        self.scene = scene_manager.history
        self.is_running = False
        self.ai_thinking_threads = []
        self.pending_responses = Queue()  # Thread-safe queue for AI responses
        
        # Lock for thread-safe message adding
        self.message_lock = threading.Lock()
        
    def start_ai_listening(self):
        """Start AI characters listening in background threads."""
        self.is_running = True
        
        for character in self.characters:
            thread = threading.Thread(
                target=self._ai_listening_loop,
                args=(character,),
                daemon=True
            )
            thread.start()
            self.ai_thinking_threads.append(thread)
    
    def stop_ai_listening(self):
        """Stop all AI listening threads."""
        self.is_running = False
        for thread in self.ai_thinking_threads:
            thread.join(timeout=2.0)
    
    def _ai_listening_loop(self, character: Character):
        """
        Background thread for each AI character.
        Continuously evaluates whether they should speak.
        """
        last_evaluation_time = time.time()
        last_spoke_time = None
        print(f"   🧵 {character.persona.name}'s listening thread started")
        
        while self.is_running:
            try:
                # Evaluate every 3 seconds to avoid overwhelming API
                time.sleep(3)
                
                # Skip if character is deliberately silent
                if character.state and character.state.is_silent:
                    continue
                
                # Get current conversation state
                with self.message_lock:
                    messages = self.scene.messages.copy()
                
                # Skip if no messages yet
                if not messages:
                    continue
                
                # COOLDOWN: If this character just spoke, wait at least 5 seconds before evaluating again
                if last_spoke_time:
                    time_since_spoke = time.time() - last_spoke_time
                    if time_since_spoke < 5:
                        continue
                
                # Check if this character was the last speaker - if so, don't speak again immediately
                if messages and messages[-1].speaker == character.persona.name:
                    # They just spoke, reset the cooldown
                    last_spoke_time = time.time()
                    continue
                
                # Check if enough time has passed since last evaluation
                current_time = time.time()
                if current_time - last_evaluation_time < 3:
                    continue
                
                last_evaluation_time = current_time
                
                # Only print occasional evaluation messages (not every one)
                if len(messages) % 5 == 0:  # Print every 5 messages
                    print(f"   💭 {character.persona.name} is thinking...")
                
                # Get story context
                story_context = None
                if self.story_manager:
                    story_context = self.story_manager.get_story_context()
                
                # Calculate time since last message
                time_since_last_message = 0
                if messages:
                    last_msg_time = messages[-1].timestamp
                    time_since_last_message = (datetime.now() - last_msg_time).total_seconds()
                
                # Decide whether to speak
                wants_to_speak, priority, reasoning, message = self.character_manager.decide_to_speak_with_timing(
                    character=character,
                    messages=messages,
                    time_since_last_message=time_since_last_message,
                    awkward_silence_threshold=self.awkward_silence_threshold,
                    story_context=story_context
                )
                
                if wants_to_speak and message:
                    # Add to queue for main thread to display
                    self.pending_responses.put({
                        'character': character,
                        'message': message,
                        'priority': priority,
                        'reasoning': reasoning,
                        'timestamp': datetime.now()
                    })
                    
                    # Update last spoke time
                    last_spoke_time = time.time()
                    print(f"   ✅ {character.persona.name} queued response: {message[:50]}...")
                else:
                    # Optional: Show why they didn't speak (only occasionally)
                    if len(messages) % 10 == 0:
                        print(f"   ⏭️  {character.persona.name} chose not to speak: {reasoning[:50]}...")
                    
            except Exception as e:
                print(f"\n⚠️  Error in {character.persona.name}'s thinking: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(5)  # Wait before retrying
    
    def add_player_message(self, content: str) -> Message:
        """
        Add player message to conversation (thread-safe).
        
        Args:
            content: What the player said
            
        Returns:
            Created Message object
        """
        with self.message_lock:
            msg = self.message_manager.create_message(
                speaker=self.player_name,
                content=content
            )
            self.message_manager.add_message(self.scene, msg)
            
            # Update character states - they're no longer waiting
            for character in self.characters:
                if character.state and character.state.focus == "waiting for Harry to respond":
                    character.state.focus = None
            
            return msg
    
    def get_pending_ai_response(self) -> Optional[dict]:
        """
        Get next pending AI response if available (non-blocking).
        
        Returns:
            Dictionary with character, message, priority, reasoning, timestamp or None
        """
        if not self.pending_responses.empty():
            return self.pending_responses.get()
        return None
    
    def process_ai_response(self, response: dict) -> Message:
        """
        Process and add an AI response to conversation (thread-safe).
        
        Args:
            response: Response dictionary from get_pending_ai_response
            
        Returns:
            Created Message object
        """
        character = response['character']
        content = response['message']
        
        with self.message_lock:
            msg = self.message_manager.create_message(
                speaker=character.persona.name,
                content=content
            )
            self.message_manager.add_message(self.scene, msg)
            
            # Update character state
            if character.state:
                character.state.last_spoken_at = datetime.now()
            
            return msg
    
    def update_character_emotional_state(self, character_name: str, mood: str, reason: str, is_silent: bool = False):
        """
        Update a character's emotional state (e.g., after being told to shut up).
        
        Args:
            character_name: Name of character
            mood: New mood (e.g., "hurt", "angry", "sad")
            reason: Why they're in this mood
            is_silent: Whether they should stop speaking
        """
        for character in self.characters:
            if character.persona.name == character_name:
                if not character.state:
                    from data_models import CharacterState
                    character.state = CharacterState(character_name=character_name)
                
                character.state.mood = mood
                character.state.is_silent = is_silent
                character.state.silence_reason = reason if is_silent else None
                break
    
    def check_for_awkward_silence(self) -> bool:
        """
        Check if there's been an awkward silence.
        
        Returns:
            True if silence has exceeded threshold
        """
        with self.message_lock:
            if not self.scene.messages:
                return False
            
            last_message = self.scene.messages[-1]
            time_since = (datetime.now() - last_message.timestamp).total_seconds()
            return time_since >= self.awkward_silence_threshold
