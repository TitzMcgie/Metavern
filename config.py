import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration settings for the roleplay system."""
    
    # API Settings - OpenRouter
    OPENROUTER_API_KEY: Optional[str] = os.getenv("OPENROUTER_API_KEY")
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    
    # Model Settings
    DEFAULT_MODEL: str = "openai/gpt-oss-20b" 
    
    MODEL_TEMPERATURE: float = 0.7
    MAX_TOKENS: int = 1024
    RESPONSE_TIMEOUT: int = 20  
    
    # Conversation Settings
    DEFAULT_CONTEXT_WINDOW: int = 100
    MAX_CONSECUTIVE_AI_TURNS: int = 3
    PRIORITY_RANDOMNESS: float = 0.1
    
    # Storage Settings
    CHAT_STORAGE_DIR: str = "Chat_Logs"
