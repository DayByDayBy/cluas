from abc import ABC, abstractmethod
from typing import Dict, Optional, List
import random
import threading
import time

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

    _provider_state_lock = threading.Lock()
    _provider_cooldown_until: Dict[str, float] = {}
    _provider_rate_limit_hits: Dict[str, int] = {}

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

    def _cooldown_key(self, provider: str, model: Optional[str] = None) -> str:
        if provider == "groq" and model:
            return f"{provider}:{model}"
        return provider

    def _is_rate_limit_error(self, exc: Exception) -> bool:
        message = str(exc).lower()
        return (
            "rate limit" in message
            or "ratelimit" in message
            or "too many requests" in message
            or "http 429" in message
            or " 429" in message
            or "status code 429" in message
        )

    def _extract_retry_after_seconds(self, exc: Exception) -> Optional[float]:
        retry_after = getattr(exc, "retry_after", None)
        if isinstance(retry_after, (int, float)):
            return float(retry_after)

        headers = None
        response = getattr(exc, "response", None)
        if response is not None:
            headers = getattr(response, "headers", None)
        if headers is None:
            headers = getattr(exc, "headers", None)

        if headers:
            value = None
            try:
                value = headers.get("retry-after") or headers.get("Retry-After")
            except Exception:
                value = None
            if value is not None:
                try:
                    return float(value)
                except Exception:
                    return None
        return None

    def _provider_in_cooldown(self, provider: str, model: Optional[str] = None) -> bool:
        key = self._cooldown_key(provider, model)
        now = time.monotonic()
        with Character._provider_state_lock:
            until = Character._provider_cooldown_until.get(key, 0.0)
        return until > now

    def _note_provider_success(self, provider: str, model: Optional[str] = None) -> None:
        key = self._cooldown_key(provider, model)
        with Character._provider_state_lock:
            Character._provider_rate_limit_hits.pop(key, None)
            Character._provider_cooldown_until.pop(key, None)

    def _note_provider_rate_limited(self, provider: str, model: Optional[str] = None, retry_after_s: Optional[float] = None) -> float:
        key = self._cooldown_key(provider, model)
        now = time.monotonic()
        with Character._provider_state_lock:
            hits = Character._provider_rate_limit_hits.get(key, 0) + 1
            Character._provider_rate_limit_hits[key] = hits

            cooldown = min(60.0, 2.0 * (2 ** min(hits - 1, 5)))
            if retry_after_s is not None:
                try:
                    cooldown = max(cooldown, float(retry_after_s))
                except Exception:
                    pass
            until = now + cooldown + (cooldown * random.uniform(0.0, 0.25))
            current_until = Character._provider_cooldown_until.get(key, 0.0)
            if until > current_until:
                Character._provider_cooldown_until[key] = until
            else:
                until = current_until
        return max(0.0, until - now)

    @abstractmethod
    async def respond(self, message: str, history: List[Dict], user_key: Optional[str] = None) -> str:
        """Return character response based on message and conversation history."""
        pass
    
    async def respond_stream(self, message: str, history: List[Dict], user_key: Optional[str] = None):
        """Stream character response in chunks (fallback to full response)."""
        # Default implementation: get full response and yield it
        full_response = await self.respond(message, history, user_key)
        yield full_response
