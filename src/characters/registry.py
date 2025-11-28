from typing import Dict, List
from src.characters.base_character import Character 

REGISTRY: Dict[str, Character] = {}

def register_instance(character: Character) -> None:
    REGISTRY[character.name.lower()] = character
    
def get_character(name: str) -> Character | None:
    return REGISTRY.get(name.lower())

def get_all_characters() -> List[Character]:
    return list(REGISTRY.values())