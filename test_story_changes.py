"""
Quick test to verify the Story class refactoring works correctly.
"""

from story_arcs import create_simple_evening_arc, create_simple_story
from managers.storyManager import StoryManager

def test_story_creation():
    """Test that stories can be created."""
    print("Testing story creation...")
    
    story = create_simple_evening_arc()
    print(f"✓ Created story: {story.title}")
    print(f"  - Beats: {len(story.beats)}")
    print(f"  - Current beat: {story.get_current_beat()['title']}")
    
    story2 = create_simple_story()
    print(f"✓ Created story: {story2.title}")
    print(f"  - Beats: {len(story2.beats)}")
    
    return story

def test_story_manager():
    """Test that StoryManager works with new Story class."""
    print("\nTesting StoryManager...")
    
    story = create_simple_evening_arc()
    manager = StoryManager(story)
    
    beat = manager.get_current_beat()
    print(f"✓ Current beat: {beat['title']}")
    
    objectives = manager.get_current_objectives()
    print(f"✓ Objectives: {len(objectives)} found")
    
    context = manager.get_story_context()
    print(f"✓ Story context generated ({len(context)} chars)")
    
    progress = manager.get_progress_summary()
    print(f"✓ Progress summary:\n{progress}")
    
    return manager

def test_story_progression():
    """Test story beat advancement."""
    print("\nTesting story progression...")
    
    story = create_simple_evening_arc()
    manager = StoryManager(story)
    
    print(f"Starting beat: {manager.get_current_beat()['title']}")
    
    # Advance story
    result = manager.advance_story()
    print(f"✓ Advanced: {result}")
    print(f"  New beat: {manager.get_current_beat()['title']}")
    
    # Advance again
    result = manager.advance_story()
    print(f"✓ Advanced: {result}")
    
    # Check if we're at the end
    if manager.get_current_beat():
        print(f"  Current beat: {manager.get_current_beat()['title']}")
    else:
        print("  Story completed!")
    
    return manager

def test_events():
    """Test event handling."""
    print("\nTesting events...")
    
    story = create_simple_story()
    print(f"Story has {len(story.beats)} beats")
    
    # Get available events
    events = story.get_available_events(0)
    print(f"✓ Available events at message 0: {len(events)}")
    
    events = story.get_available_events(10)
    print(f"✓ Available events at message 10: {len(events)}")
    
    return story

if __name__ == "__main__":
    print("="*60)
    print("STORY CLASS REFACTORING TEST")
    print("="*60)
    
    try:
        test_story_creation()
        test_story_manager()
        test_story_progression()
        test_events()
        
        print("\n" + "="*60)
        print("✓ ALL TESTS PASSED!")
        print("="*60)
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
