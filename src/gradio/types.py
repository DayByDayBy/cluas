from typing import Literal, List, Dict
from dataclasses import dataclass
from src.characters import REGISTRY

@dataclass
class BaseMessage:
    """Base message format - used internally"""
    role: Literal["user", "assistant", "system"]
    speaker: str  # "user", "corvus", "magpie", etc.
    content: str
    
    def to_llm_format(self) -> Dict:
        """Convert to LLM API format (flat)"""
        return {
            "role": self.role,
            "content": self.content
        }
    
    def to_gradio_format(self) -> Dict:
        """Convert to Gradio chatbot format (nested)"""
        return {
            "role": self.role,
            "content": [{"type": "text", "text": self.content}]
        }

@dataclass
class UIMessage(BaseMessage):
    """Extended message for UI display"""
    emoji: str = "💬"
    color: str = "#FFFFFF"
    turn_index: int = 0
    
    @classmethod
    def from_character(cls, character, content: str, turn_index: int = 0):
        """Factory method to create from Character instance"""
        return cls(
            role="assistant",
            speaker=character.name.lower(),
            content=content,
            emoji=character.emoji,
            color=character.color,
            turn_index=turn_index
        )

# Utility functions
def to_llm_history(messages: List[BaseMessage]) -> List[Dict]:
    """Convert message list to LLM API format"""
    return [msg.to_llm_format() for msg in messages]

def to_gradio_history(messages: List[BaseMessage]) -> List[Dict]:
    """Convert message list to Gradio chatbot format"""
    return [msg.to_gradio_format() for msg in messages]

def from_gradio_format(gradio_msg: Dict) -> BaseMessage:
    """Parse Gradio format back to BaseMessage"""
    role = gradio_msg["role"]

    content = gradio_msg.get("content", "")

    if isinstance(content, list):
        # original Gradio format: [{"type": "text", "text": "..."}]
        text = content[0].get("text", "") if content and isinstance(content[0], dict) else ""
    elif isinstance(content, str):
        # Our streaming path: plain string
        text = content
    else:
        text = ""

    text_strip = text.lstrip()
    
    speaker = "user" if role == "user" else "assistant"
    if speaker == "assistant":
        for char in REGISTRY.values():
            prefix = f"{char.emoji} {char.name}:".lower()
            if text_strip.lower().startswith(prefix):
                speaker = char.name
                break
    
    return BaseMessage(role=role, speaker=speaker, content=text)