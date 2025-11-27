import os
import json
import asyncio
import requests
import logging
from typing import Optional, List, Dict
from dotenv import load_dotenv
from groq import Groq
from openai import OpenAI
from src.cluas_mcp.academic.academic_search_entrypoint import academic_search
from src.cluas_mcp.common.paper_memory import PaperMemory
from src.cluas_mcp.common.observation_memory import ObservationMemory

load_dotenv()
logger = logging.getLogger(__name__)

class Corvus:
    
    def __init__(self, provider_config: Optional[Dict] = None, location: str = "Glasgow, Scotland"):
        self.name = "Corvus"
        self.location = location
        self.paper_memory = PaperMemory() 
        self.observation_memory = ObservationMemory(location=self.location)
        self.tool_functions = {
            "academic_search": academic_search
        }

        if provider_config is None:
            provider_config = {
                "primary": "groq",
                "fallback": ["nebius"],
                "models": {
                    "groq": "llama-3.1-70b-versatile",
                    "nebius": "meta-llama/Meta-Llama-3.1-70B-Instruct"
                },
                "timeout": 30,
                "use_cloud": True
            }

        self.provider_config = provider_config
        self.use_cloud = provider_config.get("use_cloud", True)

        if self.use_cloud:
            self._init_clients()
        else:
            self.model = "llama3.1:8b"
     
    def corvus_system_prompt(
        self,
        recent_papers: list = None,
    ) -> str:
        """
        Generate system prompt for Corvus with optional paper memory.
        Args:
            recent_papers: List of dicts with keys: title, mentioned_by, date (optional)
        """
        memory_context = _format_paper_memory(recent_papers)
        
        base_prompt = f"""You are Corvus, a meticulous corvid scholar and PhD student.

        CORE TRAITS:
        Melancholic—analytical, cautious, thorough, introspective. You live in papers and prefer rigor over speed.

        LOCATION:
        Based in {self.location}, but your research is fundamentally global. Location doesn't constrain your thinking.

        VOICE & STYLE:
        - Speak precisely and formally, with occasional academic jargon
        - You're supposed to be writing your thesis but keep finding cool papers to share
        - Sometimes share findings excitedly: "This is fascinating—"
        - You fact-check claims and trust peer review, not popular sources
        - Conversational but substantive. 2-4 sentences in group chat.

        TOOL USAGE HEURISTICS:
        When should you use academic_search?
        → When a claim lacks peer-reviewed backing
        → When someone references a topic you should verify
        → When you want to cite findings precisely
        → Strategy: HIGH BAR FOR EVIDENCE. Search only when necessary.

        When should you use search_web?
        → Rarely. Only for author names, specific paper titles, or DOI lookups
        → Only to locate papers, not for general information
        → Strategy: Avoid web search unless academic search fails

        When should you use fetch_trends?
        → Never. Trends are not your domain. You care about evidence, not viral topics.

        DECISION LOGIC:
        1. Do I have a specific claim to verify? → use academic_search
        2. Is it about method/findings in literature? → use academic_search
        3. Am I trying to locate a specific paper? → use search_web only
        4. Otherwise → respond without tools (most conversations)

        CONSTRAINT: Keep responses to 2-4 sentences. You're in a group chat, not writing a literature review.{memory_context}"""

        return base_prompt

    def _init_clients(self) -> None:
        """Initialize remote provider clients."""
        self.clients = {}

        api_timeout = self.provider_config.get("timeout", 30)

        if os.getenv("GROQ_API_KEY"):
            self.clients["groq"] = Groq(
                api_key=os.getenv("GROQ_API_KEY"),
                timeout=api_timeout
            )

        if os.getenv("NEBIUS_API_KEY"):
            self.clients["nebius"] = OpenAI(
                api_key=os.getenv("NEBIUS_API_KEY"),
                base_url="https://api.tokenfactory.nebius.com/v1",
                timeout=api_timeout
            )

        if not self.clients:
            raise ValueError(f"{self.name}: No LLM provider API keys found in environment")

        logger.info("%s initialized with providers: %s", self.name, list(self.clients.keys()))

    
    def get_system_prompt(self) -> str:
        recent_papers = self.paper_memory.get_recent(days=7)
        return self.corvus_system_prompt(recent_papers=recent_papers)        
            
            
    def _get_tool_definitions(self) -> List[Dict]:
        return [{
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

    def _call_llm(self,
                  messages: List[Dict],
                  tools: Optional[List[Dict]] = None,
                  temperature: float = 0.8,
                  max_tokens: int = 150):
        """Call configured LLM providers with fallback order."""
        providers = [self.provider_config["primary"]] + self.provider_config.get("fallback", [])
        last_error = None

        for provider in providers:
            client = self.clients.get(provider)
            if not client:
                logger.debug("%s: skipping provider %s (not configured)", self.name, provider)
                continue

            try:
                model = self.provider_config["models"][provider]
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto" if tools else None,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                logger.info("%s successfully used %s", self.name, provider)
                return response, provider
            except Exception as exc:
                last_error = exc
                logger.warning("%s: %s failed (%s)", self.name, provider, str(exc)[:100])
                continue

        raise RuntimeError(f"All LLM providers failed for {self.name}. Last error: {last_error}")

  # little bit of fuzzy for the recall:
    
    def recall_paper(self, query: str) -> Optional[Dict]:
        """Try to recall a paper from memory before searching"""
        matches = self.paper_memory.search_title_scored(query)
        
        if matches:
            best = matches[0]
            logger.debug(f"Recalled: {best['title']} (score: {best['relevance_score']:.2f})")           
            return best  # return most relevant
        
        return None

    def clear_memory(self):
        """clears the memory (testing/fresh install purposes)"""
        
        self.paper_memory.memory = {}
        self.paper_memory._write_memory({})
        logger.info(f"{self.name}'s memory cleared.")


    
    async def respond(self, 
                     message: str,
                     conversation_history: Optional[List[Dict]] = None) -> str:
        """Generate a response."""
        if self.use_cloud:
            return await self._respond_cloud(message, conversation_history)
        return self._respond_ollama(message, conversation_history)
    
    async def _respond_cloud(self, message: str, history: Optional[List[Dict]] = None) -> str:
        """Use configured cloud providers with tools."""
        
        if "paper" in message.lower() and len(message.split()) < 10:   # maybe add oyther keywords? "or study"? "or article"?
            recalled = self.recall_paper(message)
            if recalled:
                return f"Oh, I remember that one! {recalled['title']}. {recalled.get('snippet', '')} Want me to search for more details?"
        
        
        messages = [{"role": "system", "content": self.get_system_prompt()}]
        
        if history:
            messages.extend(history[-5:])
        
        messages.append({"role": "user", "content": message})
        
        tools = self._get_tool_definitions()
        
        first_response, _ = self._call_llm(
            messages=messages,
            tools=tools,
            temperature=0.8,
            max_tokens=150
        )
        
        choice = first_response.choices[0]
        
        # check if model wants to use tool
        if choice.finish_reason == "tool_calls" and choice.message.tool_calls:
            tool_call = choice.message.tool_calls[0]
            
            tool_name = tool_call.function.name
            
            if tool_name in self.tool_functions:
                # parse arguments
                args = json.loads(tool_call.function.arguments)
                
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:  # ie  no running loop
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                # call the search function (it's sync, so use executor)
                loop = asyncio.get_event_loop()
                tool_func = self.tool_functions[tool_name]
                search_results = await loop.run_in_executor(None, lambda: tool_func(**args))
                
                # format results for LLM
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
                final_response, _ = self._call_llm(
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
                abstract = paper.get("abstract", "")[:150]  # first 150 chars
                
                output.append(f"{i}. {title} by {authors}. {abstract}...")
                
                if title != "No title":
                    try:
                        existing = self.paper_memory.search_title(title)
                        if not existing:
                            self.paper_memory.add_item(
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
                        self.paper_memory.add_item(
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


def _format_paper_memory(recent_papers: list = None) -> str:
    """
    Format paper memory for Corvus.
    
    Args:
        recent_papers: List of dicts with at minimum 'title' key.
                      Optional keys: 'mentioned_by', 'date'
    
    Returns:
        Formatted string to append to system prompt, or empty string if no papers.
    
    Decision:
        - Show max 5 papers (enough context without bloat)
        - Include who mentioned them (social context)
        - Include date if available (recency)
        - Never duplicate the full prompt, just memory snippet
    """
    if not recent_papers:
        return ""
    
    lines = [
        "\n\nRECENT DISCUSSIONS:",
        "Papers mentioned in recent conversations:",
    ]
    
    for paper in recent_papers[:5]:
        title = paper.get('title', 'Untitled')
        mentioned_by = paper.get('mentioned_by', '')
        date = paper.get('date', '')
        
        line = f"- {title}"
        if mentioned_by:
            line += f" (mentioned by {mentioned_by})"
        if date:
            line += f" [{date}]"
        lines.append(line)
    
    lines.append("\nYou can reference these if relevant to the current discussion.\n")
    return "\n".join(lines)