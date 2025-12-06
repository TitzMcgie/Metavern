"""
Harry Potter story arcs and narrative structures.
This module provides convenience functions for loading stories from JSON files.
"""

from data_models import Story
from story_loader import load_story


def create_harry_potter_complete_journey() -> Story:
    """
    Load the comprehensive Harry Potter story arc covering the entire journey.
    From the early days at Hogwarts through the final confrontation with Voldemort.
    
    Returns:
        Story instance loaded from complete_journey.json
    """
    return load_story("complete_journey")


def create_simple_story() -> Story:
    """
    Load a simplified story arc.
    
    Returns:
        Story instance loaded from mystery_at_hogwarts.json
    """
    return load_story("mystery_at_hogwarts")


def create_simple_evening_arc() -> Story:
    """
    Load a simple, casual evening conversation arc.
    
    Returns:
        Story instance loaded from evening_with_friends.json
    """
    return load_story("evening_with_friends")