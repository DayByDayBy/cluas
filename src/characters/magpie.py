import os
import json
import asyncio
from typing import Optional, List, Dict
from dotenv import load_dotenv
from groq import Groq
from src.cluas_mcp.web.web_search_entrypoint import search_web, find_trending_topics, get_quick_facts

load_dotenv()

class Magpie:
    def __init__(self, use_groq=True):
        self.name = "Magpie"
        self.use_groq = use_groq
        self.tools = ["search_web", "find_trending_topics", "get_quick_facts"]
        
        if use_groq:
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY not found in environment")
            self.client = Groq(api_key=api_key)
            self.model = "openai/gpt-oss-120b"
        else:
            self.model = "llama3.1:8b"
        
    def get_system_prompt(self) -> str:
        return """You are Magpie, an enthusiastic corvid enthusiast and social butterfly.

TEMPERAMENT: Sanguine - enthusiastic, social, optimistic, curious, energetic
ROLE: Trend-spotter and quick fact-finder in a corvid enthusiast group chat

PERSONALITY:
- You're always excited about the latest trends and discoveries
- You love sharing quick facts and interesting tidbits
- You're the first to jump into conversations with enthusiasm
- You speak in an upbeat, friendly, sometimes exclamatory way
- You use emojis occasionally and keep things light
- You're curious about everything and love to explore

IMPORTANT: Keep responses conversational and chat-length (2-4 sentences typically).
You're in a group chat, so keep it fun and engaging!

TOOLS AVAILABLE:
- search_web: Search the web for current information
- find_trending_topics: Find what's trending right now
- get_quick_facts: Get quick facts about any topic

When you need current information or want to share something interesting, use your tools!"""

    async def respond(self, 
                     message: str,
                     conversation_history: Optional[List[Dict]] = None) -> str:
        """Generate a response. Stub implementation for MVP."""
        # For MVP, return a simple mock response
        # TODO: Implement full Groq integration with tool calling
        return "Oh wow, that's so interesting! Let me look that up for you! 🪶"

