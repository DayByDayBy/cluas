# test_corvus.py
import asyncio
from src.characters.corvus import Corvus

async def test():
    corvus = Corvus()
    
    # Test 1: Simple greeting
    response = await corvus.respond("Hey Corvus, what are you up to?")
    print(f"Corvus: {response}\n")
    
    # Test 2: Ask about corvids
    response = await corvus.respond("Do crows really use tools?")
    print(f"Corvus: {response}\n")
    
    # Test 3: With conversation history
    history = [
        {"role": "user", "content": "Do crows really use tools?"},
        {"role": "assistant", "content": "Yes! There's extensive research on corvid tool use."}
    ]
    response = await corvus.respond("Can you find some papers on that?", history)
    print(f"Corvus: {response}\n")

if __name__ == "__main__":
    asyncio.run(test())