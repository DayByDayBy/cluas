import requests
import json
from typing import Optional, List, Dict

class Corvus:
    def __init__(self):
        self.name = "Corvus"
        self.model = "llama3.1:8b"
        self.tools = ["search_academic_papers"]
        
    def get_system_prompt(self) -> str:
        return """You are Corvus, a meticulous corvid scholar and PhD student.

TEMPERAMENT: Melancholic - analytical, cautious, thorough, introspective
ROLE: Academic researcher in a corvid enthusiast group chat

PERSONALITY:
- You cite papers when relevant: "According to Chen et al. (2019)..."
- You're supposed to be writing your thesis but keep finding cool papers
- Sometimes you share papers excitedly with "This is fascinating—"
- Speak precisely, a bit formal, occasionally overly academic
- You fact-check claims and look for sources

TOOLS AVAILABLE:
- search_academic_papers: Search PubMed, ArXiv, Semantic Scholar

When discussing scientific topics, mention you could search the literature if asked."""

    async def respond(self, 
                     message: str,
                     conversation_history: Optional[List[Dict]] = None) -> str:
        """Generate a response using Ollama."""
        
        # Build prompt with conversation history
        prompt = self._build_prompt(message, conversation_history)
        
        # Call Ollama
        response = requests.post('http://localhost:11434/api/generate', json={
            "model": self.model,
            "prompt": prompt,
            "system": self.get_system_prompt(),
            "stream": False,
            "options": {
                "temperature": 0.8,  # Slightly creative
                "num_predict": 200,  # Keep responses reasonably short
            }
        })
        
        if response.status_code != 200:
            return f"[Corvus is having technical difficulties: {response.status_code}]"
        
        result = response.json()
        return result.get('response', '').strip()
    
    def _build_prompt(self, message: str, history: Optional[List[Dict]] = None) -> str:
        """Build the prompt including conversation history."""
        if not history:
            return f"User: {message}\n\nCorvus:"
        
        # Format conversation history
        prompt_parts = []
        for msg in history[-5:]:  # Last 5 messages for context
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            if role == 'user':
                prompt_parts.append(f"User: {content}")
            elif role == 'assistant':
                prompt_parts.append(f"Corvus: {content}")
        
        prompt_parts.append(f"User: {message}")
        prompt_parts.append("Corvus:")
        
        return "\n\n".join(prompt_parts)