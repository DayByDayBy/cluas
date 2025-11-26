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
# This allows the use_groq=True path to be tested without an actual key,
# but it will still raise an error if the key is explicitly checked for existence
# in the character's __init__ method (which is good, as it tests that check).
if "GROQ_API_KEY" not in os.environ:
    os.environ["GROQ_API_KEY"] = "dummy_key_for_testing"

for name, char_class in characters.items():
    print(f"Testing {name}...")

    # Test with use_groq=True
    try:
        instance = char_class(use_groq=True)
        print(f"  ✅ {name} (use_groq=True) initialized successfully.")
    except ValueError as e:
        print(f"  ❌ {name} (use_groq=True) failed to initialize: {e} (Expected if GROQ_API_KEY is missing or invalid)")
    except Exception as e:
        print(f"  ❌ {name} (use_groq=True) failed to initialize with unexpected error: {e}")

    # Test with use_groq=False (Ollama path)
    try:
        instance = char_class(use_groq=False)
        print(f"  ✅ {name} (use_groq=False) initialized successfully.")
    except Exception as e:
        print(f"  ❌ {name} (use_groq=False) failed to initialize: {e}")

print("--- Character Initialization Test Complete ---")
