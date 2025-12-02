from abc import ABC, abstractmethod
from typing import Dict, Optional, List
import os
import logging
from groq import Groq
from openai import OpenAI

logger = logging.getLogger(__name__)

class Character(ABC):
    """
    Base class for all council characters.
    Enforces required attributes and methods.
    """

    name: str
    emoji: str
    color: str
    default_location: str
    role: str
    tone: str
    delay: float = 1.0

    def __init__(self, location: Optional[str] = None, provider_config: Optional[Dict] = None):
        self.location = location or self.default_location
        self.provider_config = provider_config or {}
        self.delay = getattr(self, "delay", 1.0)
        self.clients = {}

    def _validate_api_key(self, key: str, expected_prefix: str) -> bool:
        """Validate API key format and safety."""
        if not key or len(key) < 20 or len(key) > 200:
            return False
        if not key.startswith(expected_prefix):
            return False
        # Only allow alphanumeric, dash, underscore
        return all(c.isalnum() or c in '-_' for c in key)
    
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
            raise ValueError(f"{self.name}: No LLM provider API keys found in environment")

        logger.info("%s initialized with providers: %s", self.name, list(self.clients.keys()))

    @abstractmethod
    async def respond(self, message: str, history: List[Dict], user_key: Optional[str] = None) -> str:
        """Return character response based on message and conversation history."""
        pass
    
    async def respond_stream(self, message: str, history: List[Dict], user_key: Optional[str] = None):
        """Stream character response in chunks (fallback to full response)."""
        # Default implementation: get full response and yield it
        full_response = await self.respond(message, history, user_key)
        yield full_response
    
    def get_error_message(self, error_type: str = "general") -> str:
        """
        Get character-specific error message.
        
        Args:
            error_type: Type of error ("general", "empty_response", "streaming_error")
            
        Returns:
            Character-specific error message
        """
        # Default error messages - can be overridden by subclasses
        error_messages = {
            "general": f"*{self.name} seems distracted*",
            "empty_response": f"*{self.name} seems distracted*",
            "streaming_error": f"*{self.name} seems distracted*"
        }
        return error_messages.get(error_type, error_messages["general"])
