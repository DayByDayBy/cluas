from dataclasses import dataclass

@dataclass
class Message:
    speaker: str
    emoji: str
    color: str
    content: str
    turn_index: int