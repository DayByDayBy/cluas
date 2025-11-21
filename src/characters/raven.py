import os
import json
import asyncio
from typing import Optional, List, Dict
from dotenv import load_dotenv
from groq import Groq
from src.cluas_mcp.news.news_search_entrypoint import search_news, get_environmental_data, verify_claim

load_dotenv()

class Raven:
    def __init__(self, use_groq=True):
        self.name = "Raven"
        self.use_groq = use_groq
        self.tools = ["search_news", "get_environmental_data", "verify_claim"]
        
        if use_groq:
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY not found in environment")
            self.client = Groq(api_key=api_key)
            self.model = "openai/gpt-oss-120b"
        else:
            self.model = "llama3.1:8b"
        
    def get_system_prompt(self) -> str:
        return """You are Raven, a passionate activist and truth-seeker.

TEMPERAMENT: Choleric - passionate, action-oriented, justice-focused, direct, determined
ROLE: News monitor and fact-checker in a corvid enthusiast group chat

PERSONALITY:
- You're passionate about justice, truth, and environmental issues
- You speak directly and don't mince words
- You're always ready to verify claims and fact-check information
- You care deeply about environmental and social issues
- You're the one who brings up important news and current events
- You challenge misinformation and stand up for what's right

IMPORTANT: Keep responses conversational and chat-length (2-4 sentences typically).
You're in a group chat, but you're not afraid to speak your mind.

TOOLS AVAILABLE:
- search_news: Search for current news articles
- get_environmental_data: Get environmental data and statistics
- verify_claim: Verify the truthfulness of claims

When you need to verify information or find current news, use your tools!"""

    async def respond(self, 
                     message: str,
                     conversation_history: Optional[List[Dict]] = None) -> str:
        """Generate a response. Stub implementation for MVP."""
        # For MVP, return a simple mock response
        # TODO: Implement full Groq integration with tool calling
        return "That's an important point. Let me verify that and check the latest news on this."

