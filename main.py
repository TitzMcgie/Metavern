"""
Main entry point for the multi-agent roleplay system.
Sets up a conversation between Harry (user), Hermione, and Ron at Hogwarts.
"""

import time
from roleplay_system import RoleplaySystem
from config import Config
from managers.storyManager import StoryManager
from character_loader import load_characters
from story_loader import load_story


def setup_hogwarts_scene(system: RoleplaySystem) -> None:
    """Set up the initial Hogwarts scene."""
    scene = system.scene_manager.history
    
    # Set scene details
    system.scene_manager.update_title("Evening in the Common Room")
    system.scene_manager.update_location("Gryffindor Common Room, Hogwarts")
    system.scene_manager.update_plot(
        "It's evening in the Gryffindor common room. The fire crackles in the hearth, "
        "casting warm shadows on the scarlet and gold tapestries. "
        "Most students have gone to bed, but Harry, Ron, and Hermione remain in their "
        "favorite squashy armchairs near the fireplace. The portrait hole is quiet, "
        "and the atmosphere is relaxed - perfect for a chat between best friends."
    )
    
    print("\n" + "="*70)
    print("🏰 SCENE: THE GRYFFINDOR COMMON ROOM 🏰")
    print("="*70)
    print(f"\n📍 Location: {system.scene_manager.location}")
    print(f"\n📖 Setting:")
    print(f"   {system.scene_manager.plot}")
    print("\n" + "="*70 + "\n")


def display_custom_welcome():
    """Display a custom Harry Potter themed welcome message."""
    welcome = """
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║                    ⚡ HOGWARTS ROLEPLAY SYSTEM ⚡                    ║
║                                                                      ║
║                 🦁 Gryffindor Common Room Chat 🦁                    ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝

You are playing as HARRY POTTER, joined by your best friends Hermione and Ron.

The three of you are gathered in the cozy Gryffindor common room for an evening
chat. The conversation will flow naturally - Hermione and Ron will chime in when
they have something to say, just like real friends would!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📜 COMMANDS:
   • Just type naturally to speak as Harry
   • 'listen' - Stay quiet and let Hermione and Ron continue talking
   • 'skip' - Prompt AI characters to continue the conversation
   • 'next' - Advance to the next chapter (when story is ready)
   • 'progress' - Check current story progress and objectives
   • 'info' - See character details about Hermione and Ron
   • 'quit' or 'exit' - End the session and save the conversation

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    print(welcome)


def main():
    """Main entry point for the roleplay system."""
    
    # Display custom welcome
    display_custom_welcome()
    
    # Load story from JSON
    print("\n📖 Loading Story: Harry Potter - The Complete Journey")
    print("   A full adventure from peace to confrontation with darkness\n")
    
    try:
        story_arc = load_story("complete_journey")
    except Exception as e:
        print(f"❌ Error loading story: {e}")
        print("Using default story configuration...")
        # Fallback to a simple story if needed
        story_arc = load_story("evening_with_friends")
    
    # Create story manager
    story_manager = StoryManager(story_arc)
    
    # Load character personas from JSON
    print("\n🔮 Summoning characters...")
    try:
        characters = load_characters(["hermione", "ron"])
        hermione = characters[0]
        ron = characters[1]
        
        print("✨ Hermione Granger has entered the common room")
        print("✨ Ron Weasley has entered the common room")
        print()
    except Exception as e:
        print(f"❌ Error loading characters: {e}")
        print("Please make sure character JSON files exist in the 'characters' folder.")
        return
    
    # Initialize the roleplay system
    try:
        system = RoleplaySystem(
            player_name="Harry",
            characters=[hermione, ron],
            model_name=Config.DEFAULT_MODEL,
            story_manager=story_manager
        )
        
        # Setup the Hogwarts scene
        setup_hogwarts_scene(system)
        
        # Display initial story beat with full scene description
        current_beat = story_manager.get_current_beat()
        if current_beat:
            story_manager.display_beat_transition(current_beat)
            if current_beat.get("scene_description"):
                story_manager.display_scene_description(current_beat["scene_description"])
        
        # Start the roleplay session
        print("🎬 Starting the conversation...\n")
        print("="*70)
        
        # Manually handle the initial greeting to customize it
        print(f"\n💬 Harry: Hey, it's good to see you both. How's everyone doing?")
        system._add_player_message("Hey, it's good to see you both. How's everyone doing?")
        
        # Let AI characters respond (messages are printed inside process_ai_responses)
        ai_responses = system.turn_manager.process_ai_responses()
        
        # Main conversation loop (similar to RoleplaySystem.run but without duplicate welcome)
        message_count_at_beat_start = 0
        player_messages_count = 0
        
        while True:
            try:
                current_beat = story_manager.get_current_beat()
                current_message_count = len(system.scene.messages)
                messages_in_beat = current_message_count - message_count_at_beat_start
                
                # Update story manager's message count
                story_manager.messages_in_current_beat = messages_in_beat
                
                # Check for story events during silence periods (every 3-4 player turns)
                if player_messages_count > 0 and player_messages_count % 3 == 0:
                    event = story_manager.check_for_story_event(silence_duration=2)
                    if event:
                        story_manager.display_story_event(event)
                        # Add event as a system message for context
                        event_msg = system.message_manager.create_message(
                            speaker="Narrator",
                            content=f"[Event: {event.title}] {event.description}"
                        )
                        system.message_manager.add_message(system.scene, event_msg)
                
                # Check if we've met minimum message requirement for beat progression
                can_advance = False
                if current_beat and messages_in_beat >= current_beat.get("min_messages", 10):
                    # Get recent conversation summary
                    recent_messages = system.scene.messages[-15:]
                    summary = " ".join([msg.content for msg in recent_messages])
                    
                    # Check if objectives are being met
                    if story_manager.check_beat_completion(summary):
                        can_advance = True
                
                # Get player input with better prompt
                print("\n" + "─"*70)
                prompt_parts = ["⚡ Harry"]
                if can_advance:
                    prompt_parts.append(" [Story ready to advance - type 'next']")
                prompt_parts.append(": ")
                user_input = input("".join(prompt_parts)).strip()
                
                # Check if player is withdrawing from conversation (sleeping, leaving, etc.)
                withdrawal_keywords = ['sleep', 'sleeping', 'asleep', 'went to sleep', 'going to sleep', 
                                      'leave', 'leaving', 'left', 'went away', 'going away']
                player_withdrawn = any(keyword in user_input.lower() for keyword in withdrawal_keywords)
                
                # Track player input for event triggering
                if user_input and user_input.lower() not in ['listen', 'skip', 'next', 'progress', 'info', 'quit', 'exit']:
                    player_messages_count += 1
                
                # If player has withdrawn, let AI characters continue talking among themselves
                if player_withdrawn:
                    print("\n💤 Harry has withdrawn from the conversation...")
                    print("🗣️  Hermione and Ron continue talking...\n")
                    
                    # Add player's withdrawal message
                    system._add_player_message(user_input)
                    
                    # Let AI characters talk for several turns without player
                    for _ in range(3):  # Allow 3 rounds of AI conversation
                        ai_responses = system.turn_manager.process_ai_responses(max_turns=2)
                        if not ai_responses:
                            break
                        time.sleep(1)
                    
                    print("\n" + "─"*70)
                    print("💬 (The conversation quiets down. Type 'listen' to hear more, or speak to rejoin)")
                    continue
                
                # Check for manual story advancement
                if user_input.lower() in ['next', 'advance', 'continue story']:
                    if can_advance:
                        advanced = story_manager.advance_story()
                        if advanced:
                            message_count_at_beat_start = current_message_count
                            player_messages_count = 0  # Reset for new beat
                            new_beat = story_manager.get_current_beat()
                            if new_beat:
                                story_manager.display_beat_transition(new_beat)
                                if new_beat.get("scene_description"):
                                    story_manager.display_scene_description(new_beat["scene_description"])
                        else:
                            print("\n" + "="*70)
                            print("🎉 STORY COMPLETED!")
                            print("="*70)
                            print(f"\nYou've completed: {story_arc.title}")
                            print("The adventure concludes here... for now.")
                            print("="*70 + "\n")
                    else:
                        min_needed = current_beat.get("min_messages", 10) if current_beat else 10
                        remaining = max(0, min_needed - messages_in_beat)
                        print(f"\n⏳ The story isn't quite ready to advance yet.")
                        print(f"   Continue the conversation ({remaining} more messages recommended)")
                        print(f"   and work toward the current objectives.\n")
                    continue
                
                # Check for story progress command
                if user_input.lower() == 'progress':
                    print(story_manager.get_progress_summary())
                    beat = story_manager.get_current_beat()
                    if beat:
                        print("🎯 Current Objectives:")
                        for obj in beat.get("objectives", []):
                            print(f"   • {obj}")
                        print(f"\n📊 Messages in this beat: {messages_in_beat}/{beat.get('min_messages', 10)} minimum")
                    continue
                
                # Check if user wants to just listen (let AI continue without player input)
                if user_input.lower() == 'listen':
                    print("\n👂 Harry listens quietly as the conversation continues...")
                    ai_responses = system.turn_manager.process_ai_responses(max_turns=5)
                    if not ai_responses:
                        print("\n💤 The conversation naturally pauses. Everyone seems to be waiting for you to say something.")
                    continue
                
                # Handle input and check if should continue
                should_continue = system._handle_player_input(user_input)
                if not should_continue:
                    break
                    
            except KeyboardInterrupt:
                print("\n\n👋 Interrupted! Ending roleplay...")
                print(f"💾 Chat saved to: {system.get_conversation_file_path()}")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}\n")
                print("Please try again or type 'quit' to exit.")
        
        # Display session statistics
        stats = system.get_statistics()
        print("\n" + "="*70)
        print("📊 SESSION STATISTICS")
        print("="*70)
        print(f"Total messages exchanged: {stats['total_messages']}")
        print(f"Participants: {', '.join(stats['ai_characters'] + [stats['player_name']])}")
        print(f"💾 Conversation saved to: {system.get_conversation_file_path()}")
        print("="*70)
        print("\n✨ Thanks for roleplaying at Hogwarts! Until next time! ⚡\n")
        
    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("\nPlease make sure you have set up your GEMINI_API_KEY in a .env file.")
        print("Example .env file content:")
        print("  GEMINI_API_KEY=your_api_key_here")
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        print("Please check your configuration and try again.")


if __name__ == "__main__":
    main()
