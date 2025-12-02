"""
Centralized configuration for character providers.
Eliminates duplication of default provider configs.
"""
from typing import Dict, Any

# Default provider configurations
DEFAULT_PROVIDER_CONFIG_CORVUS: Dict[str, Any] = {
    "primary": "nebius",
    "fallback": ["groq"],
    "models": {
        "nebius": "meta-llama/Llama-3.3-70B-Instruct",
        "groq": "llama-3.1-8b-instant"
    },
    "timeout": 30,
    "use_cloud": True
}

DEFAULT_PROVIDER_CONFIG_CROW: Dict[str, Any] = {
    "primary": "groq",
    "fallback": ["nebius"],
    "models": {
        "groq": "llama-3.1-8b-instant",
        "nebius": "meta-llama/Llama-3.3-70B-Instruct"
    },
    "timeout": 60,
    "use_cloud": True
}

DEFAULT_PROVIDER_CONFIG_MAGPIE: Dict[str, Any] = {
    "primary": "groq",
    "fallback": ["nebius"],
    "models": {
        "groq": "llama-3.1-8b-instant",
        "nebius": "meta-llama/Llama-3.3-70B-Instruct"
    },
    "timeout": 30,
    "use_cloud": True
}

DEFAULT_PROVIDER_CONFIG_RAVEN: Dict[str, Any] = {
    "primary": "nebius",
    "fallback": ["groq"],
    "models": {
        "nebius": "meta-llama/Llama-3.3-70B-Instruct",
        "groq": "llama-3.1-8b-instant"
    },
    "timeout": 30,
    "use_cloud": True
}

# Generic default (fallback)
DEFAULT_PROVIDER_CONFIG: Dict[str, Any] = {
    "primary": "groq",
    "fallback": ["nebius"],
    "models": {
        "groq": "llama-3.1-8b-instant",
        "nebius": "meta-llama/Llama-3.3-70B-Instruct"
    },
    "timeout": 30,
    "use_cloud": True
}

