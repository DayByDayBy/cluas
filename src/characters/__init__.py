"""Character classes for the dialectic deliberation engine."""

from .base_character import Character
from .corvus import Corvus
from .crow import Crow
from .magpie import Magpie
from .raven import Raven
from .neutral_moderator import Moderator
from .registry import register_instance, get_all_characters, REGISTRY

__all__ = [
    "Character",
    "Corvus",
    "Crow",
    "Magpie",
    "Raven",
    "Moderator",
    "register_instance",
    "get_all_characters",
    "REGISTRY",
]
