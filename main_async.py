"""
Async main entry point - natural, interruptible conversation.
You can type at ANY time, characters react naturally to timing and emotion.
"""

import time
import msvcrt  # For non-blocking keyboard input on Windows
import sys
from datetime import datetime

from data_models import CharacterPersona, CharacterState, CharacterMemory, Character
from managers.sceneManager import SceneManager
from managers.storyManager import StoryManager
from async_conversation import AsyncConversationManager
from story_arcs import create_harry_potter_complete_journey
from config import Config


def create_hermione() -> Character:
    """Create Hermione with full Character structure."""
    persona = CharacterPersona(
        name="Hermione",
        traits=[
            "Brilliant and hardworking",
            "Loyal to a fault",
            "Bossy but caring",
            "Brave despite being cautious",
            "Gets emotional when friends are in danger",
            "Perfectionist tendencies",
            "Passionate about justice and fairness"
        ],
        relationships={
            "Harry": "Best friend since first year, fiercely protective, worries about him constantly, trusts his instincts even when they seem mad",
            "Ron": "Best friend, argues with him a lot but cares deeply, gets frustrated by his laziness, secretly likes him"
        },
        speaking_style=(
            "Smart and knowledgeable but still speaks like a teenage girl, not a professor. "
            "Enthusiastic about magic and learning - gets excited when explaining things. "
            "Can be bossy and a bit of a know-it-all, but means well. "
            "Uses phrases like 'honestly', 'oh for heaven's sake', 'you two are impossible'. "
            "Gets flustered or emotional when worried about her friends. "
            "Sometimes exasperated but deeply caring - shows emotion, not just logic. "
            "Practical and solution-oriented, often has a plan. "
            "Keeps responses concise - she's explaining to friends, not writing an essay."
        ),
        background=(
            "Muggle-born witch, top of her year in every subject. "
            "Started Hogwarts knowing everything from books but had to learn about real magic and friendship. "
            "Formed the Golden Trio with Harry and Ron in first year. "
            "Founded S.P.E.W., always fights for the underdog. "
            "Comes from a loving Muggle dentist family. "
            "Has proven herself in countless dangerous situations despite being underestimated."
        ),
        goals=[
            "Help Harry succeed in his mission",
            "Protect her friends",
            "Prove that Muggle-borns are just as capable as pure-bloods",
            "Excel academically",
            "Make a difference in the wizarding world"
        ],
        knowledge_base={
            "magic": "Expert knowledge of spells, potions, and magical theory",
            "hogwarts": "Knows the castle layout, rules, and history better than most",
            "subjects": "Outstanding in all subjects, especially Charms, Transfiguration, and Ancient Runes",
            "strategy": "Excellent at planning and problem-solving"
        }
    )
    
    memory = CharacterMemory(character_name="Hermione")
    state = CharacterState(character_name="Hermione", mood="friendly")
    
    return Character(persona=persona, memory=memory, state=state)


def create_ron() -> Character:
    """Create Ron with full Character structure."""
    persona = CharacterPersona(
        name="Ron",
        traits=[
            "Fiercely loyal friend",
            "Brave but self-doubting",
            "Funny and uses humor as defense",
            "Hot-tempered when provoked",
            "Strategic thinker (chess master)",
            "Always hungry",
            "Wears his heart on his sleeve"
        ],
        relationships={
            "Harry": "Best mate, like a brother, would die for him, sometimes jealous of his fame but always comes back",
            "Hermione": "Best friend, argues constantly but it's usually playful, protective of her, secretly has feelings for her"
        },
        speaking_style=(
            "Warm, loyal, and speaks like a real teenage boy. Uses slang: 'blimey', 'bloody hell', 'mate', 'reckon', 'mental'. "
            "Makes jokes and uses humor, especially when things are tense or scary. "
            "Can be a bit insecure but fiercely protective of his friends. "
            "Gets grumpy when hungry, jealous, or feeling left out. "
            "Direct and honest - says what he thinks without fancy words. "
            "Often mentions food, Quidditch, his family, or practical concerns. "
            "Uses phrases like 'You alright?', 'Come off it', 'That's mad', 'Not likely'. "
            "Shows he cares through actions and loyalty rather than speeches."
        ),
        background=(
            "Youngest Weasley boy with five older brothers (Bill, Charlie, Percy, Fred, George) and younger sister Ginny. "
            "Pure-blood but family is considered 'blood traitors' for loving Muggles. "
            "Always got hand-me-downs growing up, family doesn't have much money. "
            "Became best friends with Harry on the Hogwarts Express first year. "
            "Gryffindor Keeper, brilliant at Wizard's Chess. "
            "Sometimes feels overshadowed but has proven his bravery time and time again. "
            "Family is everything to him."
        ),
        goals=[
            "Stand by Harry no matter what",
            "Prove himself worthy and capable",
            "Protect his friends and family",
            "Step out of his brothers' shadows",
            "Eventually tell Hermione how he feels"
        ],
        knowledge_base={
            "wizarding_world": "Grew up in wizarding culture, knows customs and traditions",
            "quidditch": "Passionate fan and player (Keeper for Gryffindor)",
            "strategy": "Brilliant chess player with tactical thinking",
            "family": "Has five older brothers and one younger sister, all with different talents"
        }
    )
    
    memory = CharacterMemory(character_name="Ron")
    state = CharacterState(character_name="Ron", mood="cheerful")
    
    return Character(persona=persona, memory=memory, state=state)


def display_welcome():
    """Display welcome message."""
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║                ⚡ REAL-TIME HOGWARTS CONVERSATION ⚡                 ║
║                                                                      ║
║                    🦁 Gryffindor Common Room 🦁                      ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝

🎮 NEW SYSTEM - NATURAL, INTERRUPTIBLE CONVERSATIONS

You can type at ANY time - even while AI characters are thinking!

✨ FEATURES:
   • Type whenever you want - no waiting for turns
   • Characters react to silence (ask again, get impatient)
   • Characters have emotions (get sad, angry, stay silent)
   • Timestamps matter - awkward silences trigger reactions
   • If Ron tells Hermione to shut up, she might actually stay quiet!

📜 COMMANDS:
   • Just start typing as Harry - press Enter to send
   • 'quit' or 'exit' - End conversation
   • '/mood [character] [mood] [reason]' - Manually set character mood
     Example: /mood Hermione sad Ron was mean to her

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")


def main():
    """Main entry point for async conversation."""
    display_welcome()
    
    # Configure Gemini API
    import google.generativeai as genai
    genai.configure(api_key=Config.GEMINI_API_KEY)
    
    # Create characters
    print("\n🔮 Summoning characters...")
    hermione = create_hermione()
    ron = create_ron()
    print("✨ Hermione Granger has entered")
    print("✨ Ron Weasley has entered\n")
    
    # Create managers
    scene_manager = SceneManager()
    story_arc = create_harry_potter_complete_journey()
    story_manager = StoryManager(story_arc)
    
    # Initialize scene
    scene = scene_manager.create_scene(
        participants=["Harry", "Hermione", "Ron"],
        location="Gryffindor Common Room, Hogwarts",
        plot="Evening conversation by the fireplace"
    )
    
    # Create async conversation manager
    conv_manager = AsyncConversationManager(
        characters=[hermione, ron],
        player_name="Harry",
        scene_manager=scene_manager,
        story_manager=story_manager,
        awkward_silence_threshold=8.0  # 8 seconds = awkward
    )
    
    print("\n" + "="*70)
    print("🏰 GRYFFINDOR COMMON ROOM - EVENING")
    print("="*70)
    print("\nThe fire crackles warmly. Ron and Hermione are sitting nearby.")
    print("\n⚡ You can start talking anytime as Harry...")
    print("="*70 + "\n")
    
    # Start AI listening in background
    conv_manager.start_ai_listening()
    
    try:
        # Main conversation loop
        input_buffer = ""
        last_check_time = time.time()
        
        while True:
            # Check for pending AI responses every 0.5 seconds
            current_time = time.time()
            if current_time - last_check_time >= 0.5:
                last_check_time = current_time
                
                # Get and display AI response if available
                ai_response = conv_manager.get_pending_ai_response()
                if ai_response:
                    character = ai_response['character']
                    message = ai_response['message']
                    timestamp = ai_response['timestamp'].strftime("%H:%M:%S")
                    
                    # Process the response
                    msg_obj = conv_manager.process_ai_response(ai_response)
                    
                    # Display with timestamp
                    print(f"\n[{timestamp}] 💬 {character.persona.name}: {message}")
                    
                    # Show if still typing
                    if input_buffer:
                        print(f"\n⚡ Harry [typing]: {input_buffer}", end='', flush=True)
            
            # Check for user input (non-blocking on Windows)
            if msvcrt.kbhit():
                char = msvcrt.getwche()
                
                if char == '\r':  # Enter key
                    if input_buffer.strip():
                        user_input = input_buffer.strip()
                        input_buffer = ""
                        print()  # New line after enter
                        
                        # Handle commands
                        if user_input.lower() in ['quit', 'exit']:
                            print("\n👋 Ending conversation...")
                            break
                        
                        # Handle mood command
                        if user_input.startswith('/mood '):
                            parts = user_input[6:].split(None, 2)
                            if len(parts) >= 3:
                                char_name, mood, reason = parts
                                is_silent = "silent" in reason.lower() or "quiet" in reason.lower() or "shut up" in reason.lower()
                                conv_manager.update_character_emotional_state(
                                    char_name,
                                    mood,
                                    reason,
                                    is_silent
                                )
                                print(f"\n✅ {char_name}'s mood updated to '{mood}' (silent={is_silent})")
                            continue
                        
                        # Add player message
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        msg = conv_manager.add_player_message(user_input)
                        print(f"[{timestamp}] ⚡ Harry: {user_input}")
                        
                elif char == '\b':  # Backspace
                    if input_buffer:
                        input_buffer = input_buffer[:-1]
                        print('\b \b', end='', flush=True)
                        
                else:
                    input_buffer += char
            
            # Small sleep to avoid CPU spinning
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted!")
    
    finally:
        # Stop AI listening threads
        conv_manager.stop_ai_listening()
        
        # Show stats
        print("\n" + "="*70)
        print("📊 CONVERSATION ENDED")
        print("="*70)
        print(f"Total messages: {len(conv_manager.scene.messages)}")
        print("="*70 + "\n")


if __name__ == "__main__":
    # Check if on Windows
    if sys.platform != 'win32':
        print("⚠️  This async version currently only works on Windows (uses msvcrt).")
        print("For other platforms, use main.py instead.")
        sys.exit(1)
    
    main()
