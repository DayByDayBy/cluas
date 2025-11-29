import os
import sys
import logging

# Add the parent directory of 'src' to sys.path to resolve imports
sys.path.append('/Users/gboa/cluas/')

# Disable logging for cleaner output
logging.getLogger().setLevel(logging.CRITICAL)

try:
    from src.characters.corvus import Corvus
    from src.characters.crow import Crow
    from src.characters.magpie import Magpie
    from src.characters.raven import Raven
except ImportError as e:
    print(f"Error importing character classes: {e}")
    sys.exit(1)

characters = {
    "Corvus": Corvus,
    "Crow": Crow,
    "Magpie": Magpie,
    "Raven": Raven,
}

print("--- Initializing Characters ---")

# Set a dummy GROQ_API_KEY for testing purposes if it's not already set
if "GROQ_API_KEY" not in os.environ:
    os.environ["GROQ_API_KEY"] = "dummy_key_for_testing"

# Define test configurations
cloud_config = {
    "primary": "groq",
    "fallback": ["nebius"],
    "models": {
        "groq": "qwen/qwen3-32b",
        "nebius": "Qwen3-30B-A3B-Instruct-2507"
    },
    "timeout": 30,
    "use_cloud": True
}

ollama_config = {
    "use_cloud": False
}

for name, char_class in characters.items():
    print(f"Testing {name}...")

    # Test with cloud providers (use_cloud=True)
    try:
        instance = char_class(provider_config=cloud_config)
        print(f"  ✅ {name} (cloud providers) initialized successfully.")
    except ValueError as e:
        print(f"  ❌ {name} (cloud providers) failed to initialize: {e} (Expected if API keys are missing)")
    except Exception as e:
        print(f"  ❌ {name} (cloud providers) failed with unexpected error: {e}")

    # Test with Ollama (use_cloud=False)
    try:
        instance = char_class(provider_config=ollama_config)
        print(f"  ✅ {name} (Ollama) initialized successfully.")
    except Exception as e:
        print(f"  ❌ {name} (Ollama) failed to initialize: {e}")
    
    # Test with default config (None - should use defaults)
    try:
        instance = char_class()
        print(f"  ✅ {name} (default config) initialized successfully.")
    except ValueError as e:
        print(f"  ⚠️  {name} (default config) failed: {e} (Expected if no API keys configured)")
    except Exception as e:
        print(f"  ❌ {name} (default config) failed with unexpected error: {e}")

print("--- Character Initialization Test Complete ---")
