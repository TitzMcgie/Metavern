# Pirate Chatbot - Captain Blackheart

A roleplay chatbot featuring Captain Blackheart, a legendary pirate ship captain, powered by Google's Gemini API.

## Features

- 🏴‍☠️ Immersive pirate character roleplay
- 💬 Full chat context management using Pydantic
- 💾 Automatic chat history saving to JSON files
- 🔄 Maintains conversation context across the entire session
- ⚓ Authentic pirate personality and dialect

## Setup

1. **Activate your conda environment:**
   ```bash
   conda activate D:\Agni\venv
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set your Gemini API key:**
   
   Get your API key from: https://makersuite.google.com/app/apikey
   
   Then set it as an environment variable:
   ```powershell
   $env:GEMINI_API_KEY='your-api-key-here'
   ```

## Usage

Run the chatbot:
```bash
python pirate_chatbot.py
```

Type your messages to chat with Captain Blackheart. Type `quit`, `exit`, or `goodbye` to end the conversation.

## Chat History

All conversations are automatically saved in the `chat_logs/` directory with the format:
```json
[
  {
    "user": "Hello Captain!",
    "timestamp": "2025-11-11T..."
  },
  {
    "model": "Ahoy there, matey!...",
    "timestamp": "2025-11-11T..."
  }
]
```

## How It Works

1. **Context Management**: The entire chat history is sent to Gemini with each request, maintaining full conversation context
2. **Pydantic Models**: Uses Pydantic for data validation and structured chat history
3. **System Prompt**: A detailed character prompt ensures Captain Blackheart stays in character
4. **Persistent Storage**: Every exchange is saved to a JSON file for later reference

Enjoy your adventure on the high seas! ⚓🏴‍☠️
