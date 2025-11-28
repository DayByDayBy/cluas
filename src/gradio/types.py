from dataclasses import dataclass
from typing import Literal

@dataclass
class BaseMessage:
    role: Literal["user", "assistant", "system"]
    speaker: str        # "corvus" | "magpie" | "user" | etc.
    content: str
    
@dataclass
class UIMessage(BaseMessage):    
    emoji: str
    color: str
    turn_index: int = 0