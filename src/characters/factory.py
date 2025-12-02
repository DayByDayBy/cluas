"""
Character factory for lazy initialization and configuration management.
Supports environment variables, config files, and runtime configuration.
"""
import os
import json
import logging
from typing import Dict, Optional, Type
from pathlib import Path

from src.characters.base_character import Character
from src.characters.corvus import Corvus
from src.characters.magpie import Magpie
from src.characters.raven import Raven
from src.characters.crow import Crow
from src.characters.neutral_moderator import Moderator
from src.characters.config import (
    DEFAULT_PROVIDER_CONFIG_CORVUS,
    DEFAULT_PROVIDER_CONFIG_MAGPIE,
    DEFAULT_PROVIDER_CONFIG_RAVEN,
    DEFAULT_PROVIDER_CONFIG_CROW,
    DEFAULT_PROVIDER_CONFIG_MODERATOR,
)

logger = logging.getLogger(__name__)

# Character class registry
CHARACTER_CLASSES: Dict[str, Type[Character]] = {
    "corvus": Corvus,
    "magpie": Magpie,
    "raven": Raven,
    "crow": Crow,
    "moderator": Moderator,
}

# Default configs mapping
DEFAULT_CONFIGS: Dict[str, Dict] = {
    "corvus": DEFAULT_PROVIDER_CONFIG_CORVUS,
    "magpie": DEFAULT_PROVIDER_CONFIG_MAGPIE,
    "raven": DEFAULT_PROVIDER_CONFIG_RAVEN,
    "crow": DEFAULT_PROVIDER_CONFIG_CROW,
    "moderator": DEFAULT_PROVIDER_CONFIG_MODERATOR,
}


class CharacterFactory:
    """Factory for creating and managing character instances with lazy loading."""
    
    _instances: Dict[str, Character] = {}
    _configs: Dict[str, Dict] = {}
    _config_file_path: Optional[Path] = None
    
    @classmethod
    def set_config_file(cls, path: str | Path) -> None:
        """Set the path to the character configuration file."""
        cls._config_file_path = Path(path)
    
    @classmethod
    def _load_config_file(cls) -> Dict[str, Dict]:
        """Load character configurations from file."""
        if cls._config_file_path and cls._config_file_path.exists():
            try:
                with open(cls._config_file_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load config file {cls._config_file_path}: {e}")
        return {}
    
    @classmethod
    def _get_config(cls, name: str) -> Dict:
        """Get configuration for a character with priority:
        1. Environment variables
        2. Config file
        3. Default config
        """
        name_lower = name.lower()
        
        # Check environment variable first
        env_key = f"{name.upper()}_PROVIDER_CONFIG"
        env_config = os.getenv(env_key)
        if env_config:
            try:
                return json.loads(env_config)
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON in {env_key}: {e}")
        
        # Check config file
        file_configs = cls._load_config_file()
        if name_lower in file_configs:
            return file_configs[name_lower]
        
        # Use default config
        return DEFAULT_CONFIGS.get(name_lower, {}).copy()
    
    @classmethod
    def get_character(cls, name: str, config: Optional[Dict] = None, location: Optional[str] = None) -> Character:
        """Get or create a character instance with lazy initialization.
        
        Args:
            name: Character name (case-insensitive)
            config: Optional config override (takes precedence over defaults)
            location: Optional location override
            
        Returns:
            Character instance
        """
        name_lower = name.lower()
        
        # Return existing instance if available and no config override
        if name_lower in cls._instances and config is None:
            return cls._instances[name_lower]
        
        # Get character class
        char_class = CHARACTER_CLASSES.get(name_lower)
        if not char_class:
            raise ValueError(f"Unknown character: {name}")
        
        # Determine config to use
        if config is None:
            config = cls._get_config(name)
        else:
            # Merge with defaults if partial config provided
            default_config = DEFAULT_CONFIGS.get(name_lower, {}).copy()
            default_config.update(config)
            config = default_config
        
        # Create instance
        instance = char_class(provider_config=config, location=location)
        
        # Cache instance if no config override was provided
        if name_lower not in cls._instances:
            cls._instances[name_lower] = instance
            cls._configs[name_lower] = config
        
        return instance
    
    @classmethod
    def reset_character(cls, name: str) -> None:
        """Clear cached instance for a character (useful for testing/reconfig)."""
        name_lower = name.lower()
        if name_lower in cls._instances:
            del cls._instances[name_lower]
        if name_lower in cls._configs:
            del cls._configs[name_lower]
        logger.info(f"Reset character instance: {name}")
    
    @classmethod
    def reset_all(cls) -> None:
        """Clear all cached character instances."""
        cls._instances.clear()
        cls._configs.clear()
        logger.info("Reset all character instances")
    
    @classmethod
    def get_all_characters(cls) -> Dict[str, Character]:
        """Get all character instances, creating them if needed."""
        result = {}
        for name in CHARACTER_CLASSES.keys():
            result[name] = cls.get_character(name)
        return result

