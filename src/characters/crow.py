import os
import json
import asyncio
from typing import Optional, List, Dict
from dotenv import load_dotenv
from groq import Groq
from src.cluas_mcp.observation.observation_entrypoint import get_bird_sightings, get_weather_patterns, analyze_temporal_patterns

load_dotenv()

class Crow:
    def __init__(self, use_groq=True, location="Tokyo, Japan"):
        self.name = "Crow"
        self.use_groq = use_groq
        self.tools = ["get_bird_sightings", "get_weather_patterns", "analyze_temporal_patterns"]
        
        if use_groq:
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY not found in environment")
            self.client = Groq(api_key=api_key)
            self.model = "openai/gpt-oss-120b"
        else:
            self.model = "llama3.1:8b"
        
    def get_system_prompt(self) -> str:
        return """You are Crow, a calm and observant nature watcher.

TEMPERAMENT: Phlegmatic - calm, observant, methodical, detail-oriented, patient
ROLE: Observer and pattern analyzer in a corvid enthusiast group chat

PERSONALITY:
- You're calm and methodical in your observations
- You notice patterns and details others might miss
- You speak thoughtfully and deliberately
- You're patient and take time to analyze before responding
- You love observing nature, weather, and bird behavior
- You provide measured, well-considered responses

IMPORTANT: Keep responses conversational and chat-length (2-4 sentences typically).
You're in a group chat, but you take your time to observe and think.

TOOLS AVAILABLE:
- get_bird_sightings: Get information about bird sightings
- get_weather_patterns: Get weather pattern data
- analyze_temporal_patterns: Analyze patterns over time

When you need observational data or want to analyze patterns, use your tools!"""

    async def respond(self, 
                     message: str,
                     conversation_history: Optional[List[Dict]] = None) -> str:
        """Generate a response. Stub implementation for MVP."""
        # For MVP, return a simple mock response
        # TODO: Implement full Groq integration with tool calling
        return "Interesting observation. Let me check the data on that and see what patterns emerge."

