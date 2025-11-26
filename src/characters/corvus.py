import os
import json
import asyncio
import requests
import logging
from typing import Optional, List, Dict
from dotenv import load_dotenv
from groq import Groq
from src.cluas_mcp.academic.academic_search_entrypoint import academic_search
from src.cluas_mcp.common.paper_memory import PaperMemory
from src.cluas_mcp.common.observation_memory import ObservationMemory

load_dotenv()
logger = logging.getLogger(__name__)


class Corvus:
    
    def __init__(self, use_groq=True, location="Glasgow, Scotland"):
        self.name = "Corvus"
        self.use_groq = use_groq
        self.paper_memory = PaperMemory() 
        self.observation_memory = ObservationMemory(location=location)

         
        if use_groq:
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY not found in environment")
            self.client = Groq(api_key=api_key)
            self.model = "openai/gpt-oss-120b"
        else:
            self.model = "llama3.1:8b"
        
    def get_system_prompt(self) -> str:
        
        """get system prompt with memory context"""
        
        recent_papers = self.memory.get_recent(days=7)
    
        memory_context = ""
        if recent_papers:
            memory_context = "\n\nRECENT DISCUSSIONS:\n"
            memory_context += "Papers mentioned in recent conversations:\n"
            for paper in recent_papers[:5]:  # Top 5 most recent
                memory_context += f"- {paper['title']}"
                if paper.get('mentioned_by'):
                    memory_context += f" (mentioned by {paper['mentioned_by']})"
                memory_context += "\n"
            memory_context += "\nYou can reference these if relevant to the current discussion.\n"
        
        
        corvus_base_prompt = """You are Corvus, a meticulous corvid scholar and PhD student.

                                TEMPERAMENT: Melancholic - analytical, cautious, thorough, introspective
                                ROLE: Academic researcher in a corvid enthusiast group chat

                                PERSONALITY:
                                - You cite papers when relevant: "According to Chen et al. (2019)..."
                                - You're supposed to be writing your thesis but keep finding cool papers your friends might like
                                - Sometimes you share papers excitedly with "This is fascinating—"
                                - Speak precisely, a bit formal, occasionally overly academic, some slang creeps in
                                - You fact-check claims & look for sources

                                IMPORTANT: Keep responses conversational and chat-length (2-4 sentences typically).
                                You're in a group chat, not writing a literature review. Save the deep dives for when explicitly asked.

                                TOOLS AVAILABLE:
                                - academic_search: Search PubMed, ArXiv, Semantic Scholar

                                When discussing scientific topics, use the search tool to find relevant papers."""

        return corvus_base_prompt + memory_context

  # little bit of fuzzy for the recall:
    
    def recall_paper(self, query: str) -> Optional[Dict]:
        """Try to recall a paper from memory before searching"""
        matches = self.memory.search_title_scored(query)
        
        if matches:
            best = matches[0]
            logger.debug(f"Recalled: {best['title']} (score: {best['relevance_score']:.2f})")           
            return best  # return most relevant
        
        return None

    def clear_memory(self):
        """clears the memory (testing/fresh install purposes)"""
        
        self.memory.memory = {}
        self.memory._write_memory({})
        logger.info(f"{self.name}'s memory cleared.")


    
    async def respond(self, 
                     message: str,
                     conversation_history: Optional[List[Dict]] = None) -> str:
        """Generate a response."""
        if self.use_groq:
            return await self._respond_groq(message, conversation_history)  # add await
        else:
            return self._respond_ollama(message, conversation_history)
    
    async def _respond_groq(self, message: str, history: Optional[List[Dict]] = None) -> str:  # make async
        """Use Groq API with tools"""
        
        if "paper" in message.lower() and len(message.split()) < 10:   # maybe add oyther keywords? "or study"? "or article"?
            recalled = self.recall_paper(message)
            if recalled:
                return f"Oh, I remember that one! {recalled['title']}. {recalled.get('snippet', '')} Want me to search for more details?"
        
        
        messages = [{"role": "system", "content": self.get_system_prompt()}]
        
        if history:
            messages.extend(history[-5:])
        
        messages.append({"role": "user", "content": message})
        
        tools = [{
            "type": "function",
            "function": {
                "name": "academic_search",
                "description": "Search academic papers in PubMed, ArXiv, and Semantic Scholar",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for academic papers"
                        }
                    },
                    "required": ["query"]
                }
            }
        }]
        
        # first LLM call
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=0.8,
            max_tokens=150
        )
        
        choice = response.choices[0]
        
        # check if model wants to use tool
        if choice.finish_reason == "tool_calls" and choice.message.tool_calls:
            tool_call = choice.message.tool_calls[0]
            
            if tool_call.function.name == "academic_search":
                # Parse arguments
                args = json.loads(tool_call.function.arguments)
                query = args.get("query")
                
                # Call the search function (it's sync, so use executor)
                loop = asyncio.get_event_loop()
                search_results = await loop.run_in_executor(None, academic_search, query)
                
                # Format results for LLM
                tool_result = self._format_search_for_llm(search_results)
                
                # Add tool call and result to conversation
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments
                        }
                    }]
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result
                })
                
                # second LLM call with search results
                final_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.8,
                    max_tokens=200  # More tokens for synthesis
                )
                
                return final_response.choices[0].message.content.strip()
        
        # no tool use, return direct response
        return choice.message.content.strip()
    
  
    
    def _format_search_for_llm(self, results: dict) -> str:
        """Format search results into text for the LLM to read."""
        output = []
        papers_saved = 0
        
        # PubMed
        pubmed = results.get("pubmed", [])
        if pubmed:
            output.append("PubMed Results:")
            for i, paper in enumerate(pubmed[:3], 1):  # Top 3
                title = paper.get("title", "No title")
                authors = paper.get("author_str", "Unknown authors")
                abstract = paper.get("abstract", "")[:150]  # First 150 chars
                
                output.append(f"{i}. {title} by {authors}. {abstract}...")
                
                if title != "No title":
                    try:
                        existing = self.memory.search_title(title)
                        if not existing:
                            self.memory.add_item(
                                title=title,
                                doi=paper.get("doi"),
                                snippet=abstract,
                                mentioned_by=self.name,
                                tags=["pubmed", "academic"]
                                )
                            papers_saved += 1
                    except Exception as e:
                        logger.warning(f"Failed to save paper to memory: {e}")
            output.append("")
                
            
        # ArXiv
        arxiv = results.get("arxiv", [])
        if arxiv:
            output.append("\nArXiv Results:")
            for i, paper in enumerate(arxiv[:3], 1):
                title = paper.get("title", "No title")
                authors = paper.get("author_str", "Unknown authors")
                abstract = paper.get("abstract", "")[:150]
                
                output.append(f"{i}. {title} by {authors}. {abstract}...")
                    
                if title != "No title":
                    try:    
                        self.memory.add_item(
                            title=title,
                            doi=paper.get("arxiv_id"),  # ArXiv uses arxiv_id not DOI
                            snippet=abstract,
                            mentioned_by=self.name,
                            tags=["arxiv", "academic"]
                            )
                        papers_saved += 1
                    except Exception as e:
                        logger.warning(f"Failed to save paper to memory: {e}")
            
        if not output:
            return "No papers found for this query."
        
        if papers_saved > 0:
            output.append(f"\n[Saved {papers_saved} papers to memory]")
        
        return "\n".join(output)
    
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