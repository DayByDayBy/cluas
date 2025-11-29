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

    @abstractmethod
    async def respond(self, message: str, history: List[Dict]) -> str:
        """Return character response based on message and conversation history."""
        pass
