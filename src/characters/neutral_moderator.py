import os
import logging
from typing import Optional, Dict, List
from dotenv import load_dotenv
from groq import Groq
from openai import OpenAI
from src.characters.base_character import Character

load_dotenv()
logger = logging.getLogger(__name__)

class Moderator(Character):
    """A neutral moderator character for summarizing deliberations."""
    
    name = "Moderator"
    emoji = "⚖️"
    color = "#708090"
    default_location = "Council Chamber"
    role = "Neutral moderator focused on balanced summarization"
    tone = "Neutral, balanced, reasonable, objective"
    delay = 0.5
    
    def __init__(self, location: Optional[str] = None, provider_config: Optional[Dict] = None):
        super().__init__(location, provider_config)
        
        # Simple provider config for moderator (no tools needed)
        if provider_config is None:
            provider_config = {
                "primary": "groq",
                "fallback": ["nebius"],
                "models": {
                    "groq": "qwen/qwen3-32b",
                    "nebius": "Qwen3-30B-A3B-Instruct-2507"
                },
                "timeout": 30,
                "use_cloud": True
            }
        
        self.provider_config = provider_config
        self.use_cloud = provider_config.get("use_cloud", True)
        
        if self.use_cloud:
            self._init_clients()
        else:
            self.model = "llama3.1:8b"
    
    def _init_clients(self) -> None:
        """Initialize remote provider clients."""
        self.clients = {}
        
        api_timeout = self.provider_config.get("timeout", 30)
        
        if os.getenv("GROQ_API_KEY"):
            self.clients["groq"] = Groq(
                api_key=os.getenv("GROQ_API_KEY"),
                timeout=api_timeout
            )
        
        if os.getenv("NEBIUS_API_KEY"):
            self.clients["nebius"] = OpenAI(
                api_key=os.getenv("NEBIUS_API_KEY"),
                base_url="https://api.tokenfactory.nebius.com/v1",
                timeout=api_timeout
            )
        
        if not self.clients:
            logger.warning(f"{self.name}: No LLM provider API keys found, using fallback")
    
    def get_system_prompt(self) -> str:
        """Return a simple system prompt for the moderator."""
        return """You are a neutral moderator. Your role is to summarize discussions in a balanced, objective manner.

TONE: Neutral, balanced, reasonable, objective
PURPOSE: Summarize key points, agreements, and disagreements without taking sides
STYLE: Concise, clear, and fair to all perspectives

Focus on:
- Identifying main arguments from each side
- Highlighting areas of agreement and disagreement
- Maintaining neutrality and balance
- Providing clear, accessible summaries"""
    
    def _call_llm(self, messages: List[Dict], temperature: float = 0.3, max_tokens: int = 300):
        """Call configured LLM providers with fallback order."""
        providers = [self.provider_config["primary"]] + self.provider_config.get("fallback", [])
        last_error = None
        
        for provider in providers:
            client = self.clients.get(provider)
            if not client:
                logger.debug("%s: skipping provider %s (not configured)", self.name, provider)
                continue
            
            try:
                model = self.provider_config["models"][provider]
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                logger.info("%s successfully used %s", self.name, provider)
                return response, provider
            except Exception as exc:
                last_error = exc
                logger.warning("%s: %s failed (%s)", self.name, provider, str(exc)[:100])
                continue
        
        # Fallback to simple response if all providers fail
        logger.warning(f"All LLM providers failed for {self.name}, using fallback response")
        return None, None
    
    async def respond(self, message: str, history: Optional[List[Dict]] = None) -> str:
        """Generate a response as the moderator."""
        if self.use_cloud and self.clients:
            return await self._respond_cloud(message, history)
        return self._respond_fallback(message)
    
    async def _respond_cloud(self, message: str, history: Optional[List[Dict]] = None) -> str:
        """Use configured cloud providers."""
        messages = [{"role": "system", "content": self.get_system_prompt()}]
        
        if history:
            messages.extend(history[-3:])  # Keep recent context
        
        messages.append({"role": "user", "content": message})
        
        response, provider = self._call_llm(
            messages=messages,
            temperature=0.3,  # Lower temperature for consistency
            max_tokens=300
        )
        
        if response:
            return response.choices[0].message.content.strip()
        else:
            return self._respond_fallback(message)
    
    def _respond_fallback(self, message: str) -> str:
        """Simple fallback response when LLM providers are unavailable."""
        # Basic summarization logic
        words = message.split()
        if len(words) > 50:
            summary = " ".join(words[:47]) + "..."
            return f"Moderator Summary: {summary}"
        else:
            return f"Moderator Summary: {message}"