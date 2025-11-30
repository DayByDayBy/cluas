from abc import ABC, abstractmethod
from typing import Dict, Optional, List

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

    def _validate_api_key(self, key: str, expected_prefix: str) -> bool:
        """Validate API key format and safety."""
        if not key or len(key) < 20 or len(key) > 200:
            return False
        if not key.startswith(expected_prefix):
            return False
        # Only allow alphanumeric, dash, underscore
        return all(c.isalnum() or c in '-_' for c in key)

    @abstractmethod
    async def respond(self, message: str, history: List[Dict], user_key: Optional[str] = None) -> str:
        """Return character response based on message and conversation history."""
        pass
