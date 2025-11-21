import os
from groq import Groq

class Corvus:
    def __init__(self, use_groq=True):
        self.name = "Corvus"
        self.use_groq = use_groq
        
        if use_groq:
            self.client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
            self.model = "llama-3.1-70b-versatile"  # mixtral-8x7b also not a bad shout
        else:
            self.model = "llama3.1:8b"
    
    async def respond(self, message: str, conversation_history=None) -> str:
        if self.use_groq:
            return await self._respond_groq(message, conversation_history)
        else:
            return await self._respond_ollama(message, conversation_history)
    
    async def _respond_groq(self, message: str, history=None):
        messages = [{"role": "system", "content": self.get_system_prompt()}]
        
        if history:
            messages.extend(history[-5:])
        
        messages.append({"role": "user", "content": message})
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.8,
            max_tokens=300
        )
        
        return response.choices[0].message.content.strip()