
import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from roleplay_system import RoleplaySystem
from loaders.character_loader import CharacterLoader
from loaders.story_loader import StoryLoader
from managers.storyManager import StoryManager
from config import Config

app = FastAPI(title="Metavern API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state (for demo purposes)
class GameState:
    system: Optional[RoleplaySystem] = None

game_state = GameState()

class InitRequest(BaseModel):
    player_name: str
    story_dir: str = "Pirate Adventure"
    characters: List[str] = ["marina", "jack", "captain", "martin"]

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    messages: List[dict]

@app.post("/api/init")
async def init_game(request: InitRequest):
    try:
        # Load story
        story_loader = StoryLoader(request.story_dir)
        story_arc = None
        try:
            story_arc = story_loader.load_story()
        except Exception as e:
            print(f"Warning: Could not load story: {e}")

        # Load characters
        character_loader = CharacterLoader(request.story_dir)
        characters = character_loader.load_multiple_characters(request.characters)

        # Initialize System
        game_state.system = RoleplaySystem(
            player_name=request.player_name,
            characters=characters,
            story_manager=StoryManager(story_arc) if story_arc else None,
            initial_location="Aboard the Sea Serpent",
            initial_scene_description="The sun is setting over the endless ocean..."
        )
        
        return {"status": "initialized", "message": "Game started successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from data_models import Message, Action

@app.post("/api/chat")
async def chat(request: ChatRequest):
    if not game_state.system:
        raise HTTPException(status_code=400, detail="Game not initialized")
    
    user_input = request.message
    system = game_state.system
    
    # 1. Record User Message
    user_message = Message(
        character=system.player_name,
        dialouge=user_input,
        action_description="Speaking"
    )
    system.timeline_manager.add_event(system.timeline, user_message)
    
    # 2. Check for DM Mention (@Martin)
    # If explicitly mentioned, prioritize Martin
    force_martin = "martin" in user_input.lower()
    
    responses = []
    
    if force_martin:
        # Find Martin
        martin = next((c for c in system.ai_characters if c.persona.name.lower() == "martin"), None)
        if martin:
             # Force a turn for Martin
             pass

    # 3. Let TurnManager handle AI responses
    turn_manager = system.turn_manager
    
    # Collect decisions
    try:
        decisions = turn_manager._collect_speaking_decisions()
        
        # Boost mentioned character priority
        if force_martin:
             for i, (char, decision) in enumerate(decisions):
                 if char.persona.name.lower() == "martin":
                     # Boost priority by adding 1.0 (ensures he's likely top)
                     resp_type, prio, reas, dial, act = decision
                     decisions[i] = (char, (resp_type, prio + 2.0, reas, dial, act))
                     
        # Sort by priority
        decisions.sort(key=lambda x: x[1][1], reverse=True)
    except Exception as e:
        print(f"Error collecting decisions: {e}")
        decisions = []
    
    new_messages = []
    
    # Allow multiple characters to speak (up to 3)
    count = 0
    for character, (response_type, priority, reasoning, dialogue, action) in decisions:
        if count >= 3: 
            break
            
        if response_type == "speak":
            msg = Message(
                character=character.persona.name,
                dialouge=dialogue,
                action_description=action or ""
            )
            system.timeline_manager.add_event(system.timeline, msg)
            
            new_messages.append({
                "character": character.persona.name,
                "content": dialogue,
                "action": action,
                "type": "message"
            })
            
            # Update memory
            system.character_manager.broadcast_event_to_characters(system.ai_characters, msg)
            count += 1
            
        elif response_type == "act":
            act_event = Action(
                character=character.persona.name,
                description=action
            )
            system.timeline_manager.add_event(system.timeline, act_event)

            new_messages.append({
                "character": character.persona.name,
                "content": action, # For acts, content is description
                "type": "action"
            })
            system.character_manager.broadcast_event_to_characters(system.ai_characters, act_event)
            count += 1

    return {"messages": new_messages}

@app.get("/api/history")
async def get_history():
    if not game_state.system:
        return {"messages": []}
    
    # Convert timeline events to simple format
    history = []
    for event in game_state.system.timeline.events:
        if event.type == "message":
            history.append({
                "character": event.character,
                "content": event.dialouge,
                "action": event.action_description,
                "type": "message",
                "timestamp": event.timestamp.isoformat()
            })
        elif event.type == "action":
            history.append({
                "character": event.character,
                "content": event.description,
                "type": "action",
                "timestamp": event.timestamp.isoformat()
            })
        elif event.type == "scene":
             history.append({
                "character": "System",
                "content": f"[{event.location}] {event.description}",
                "type": "scene",
                "timestamp": event.timestamp.isoformat()
            })
            
    return {"messages": history}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
