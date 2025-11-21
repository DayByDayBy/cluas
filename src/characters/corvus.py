import os
import requests
from typing import Optional, List, Dict
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

class Corvus:
    def __init__(self, use_groq=True):
        self.name = "Corvus"
        self.use_groq = use_groq
        self.tools = ["search_academic_papers"]
        
        if use_groq:
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY not found in environment")
            self.client = Groq(api_key=api_key)
            self.model = "llama-3.1-70b-versatile"
        else:
            self.model = "llama3.1:8b"
        
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
        """Generate a response."""
        if self.use_groq:
            return self._respond_groq(message, conversation_history)
        else:
            return self._respond_ollama(message, conversation_history)
    
    def _respond_groq(self, message: str, history: Optional[List[Dict]] = None) -> str:
        """Use Groq API."""
        messages = [{"role": "system", "content": self.get_system_prompt()}]
        
        if history:
            messages.extend(history[-5:])  # Last 5 for context
        
        messages.append({"role": "user", "content": message})
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.8,
            max_tokens=300
        )
        
        return response.choices[0].message.content.strip()
    
    def _respond_ollama(self, message: str, history: Optional[List[Dict]] = None) -> str:
        """Use Ollama."""
        prompt = self._build_prompt(message, history)
        
        response = requests.post('http://localhost:11434/api/generate', json={
            "model": self.model,
            "prompt": prompt,
            "system": self.get_system_prompt(),
            "stream": False,
            "options": {
                "temperature": 0.8,
                "num_predict": 200,
            }
        })
        
        if response.status_code != 200:
            return f"[Corvus is having technical difficulties: {response.status_code}]"
        
        result = response.json()
        return result.get('response', '').strip()
    
    def _build_prompt(self, message: str, history: Optional[List[Dict]] = None) -> str:
        """Build prompt for Ollama."""
        if not history:
            return f"User: {message}\n\nCorvus:"
        
        prompt_parts = []
        for msg in history[-5:]:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            if role == 'user':
                prompt_parts.append(f"User: {content}")
            elif role == 'assistant':
                prompt_parts.append(f"Corvus: {content}")
        
        prompt_parts.append(f"User: {message}")
        prompt_parts.append("Corvus:")
        
        return "\n\n".join(prompt_parts)