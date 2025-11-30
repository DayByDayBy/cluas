import os
import json
import asyncio
import logging
import requests
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from groq import Groq
from openai import OpenAI
from src.cluas_mcp.news.news_search import verify_news
from src.cluas_mcp.web.explore_web import explore_web
from src.cluas_mcp.web.trending import get_trends
from src.cluas_mcp.common.paper_memory import PaperMemory
from src.cluas_mcp.common.observation_memory import ObservationMemory
from src.cluas_mcp.common.check_local_weather import check_local_weather
from src.prompts.character_prompts import raven_system_prompt
from src.characters.base_character import Character

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Raven(Character):
    name = "Raven"
    emoji = "🦅"
    color = "#2E8B57"
    default_location = "Seattle, WA"
    delay = 1.0
    def __init__(self, provider_config: Optional[Dict] = None, location: Optional[str] = None):
        super().__init__(location, provider_config)
        
        self.role = "Choleric activist challenging misinformation and demanding accountability"
        self.tone = "Direct, assertive, justice-oriented, calls out weak claims"
        self.paper_memory = PaperMemory()
        self.observation_memory = ObservationMemory(location=location)
        self.tool_functions = {
            "verify_news": verify_news,
            "explore_web": explore_web,
            "get_trends": get_trends,
            "check_local_weather": check_local_weather

        }
        
        # Default provider priority
        if provider_config is None:
            provider_config = {
                "primary": "groq",
                "fallback": ["nebius"],
                "models": {
                    "groq": "qwen/qwen3-32b",
                    "nebius": "Qwen3-30B-A3B-Instruct-2507"
                },
                "timeout": 30,
                "use_cloud": True
            }
        
        self.provider_config = provider_config
        self.use_cloud = provider_config.get("use_cloud", True)
        
        if self.use_cloud:
            self._init_clients()
        else:
            # Local ollama fallback
            self.model = "llama3.1:8b"
    
    def _init_clients(self):
        """Initialize all available provider clients"""
        self.clients = {}
        
        # Groq
        if os.getenv("GROQ_API_KEY"):
            self.clients["groq"] = Groq(
                api_key=os.getenv("GROQ_API_KEY"),
                timeout=self.provider_config.get("timeout", 30)
            )
        
        # Nebius Token Factory (OpenAI-compatible)
        if os.getenv("NEBIUS_API_KEY"):
            self.clients["nebius"] = OpenAI(
                api_key=os.getenv("NEBIUS_API_KEY"),
                base_url="https://api.tokenfactory.nebius.com/v1",
                timeout=self.provider_config.get("timeout", 30)
            )
        
        # Log which providers are available
        available = list(self.clients.keys())
        if not available:
            raise ValueError(f"{self.name}: No LLM provider API keys found in environment")
        logger.info(f"{self.name} initialized with providers: {available}")
        
    def get_system_prompt(self) -> str:
        # Raven doesn't have a dedicated source memory yet, but could be added
        return raven_system_prompt(location=self.location, recent_sources=None)

    def _get_tool_definitions(self) -> List[Dict]:
        """Return tool definitions for function calling"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "verify_news",
                    "description": "Search for current news articles and reports",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Topic or question to search in news outlets"
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of articles to return (default 5)"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "explore_web",
                    "description": "Search the broader web for claims, sources, and facts",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query for the web"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_trends",
                    "description": "Fetch trending topics for a category",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "category": {
                                "type": "string",
                                "description": "Trend category (e.g., 'news', 'climate', 'tech')"
                            }
                        },
                        "required": ["category"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "check_local_weather",
                    "description": "Get current weather conditions for a location",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "Location to get weather for (e.g., 'Washington, DC')"
                            }
                        },
                        "required": []
                    }
                }
            }
        ]

    def _call_llm(self, messages: List[Dict], tools: Optional[List[Dict]] = None, 
                  temperature: float = 0.8, max_tokens: int = 150) -> tuple:
        """Call LLM with automatic fallback"""
        providers = [self.provider_config["primary"]] + self.provider_config["fallback"]
        last_error = None
        
        for provider in providers:
            if provider not in self.clients:
                logger.debug(f"{self.name}: Skipping {provider} - not configured")
                continue
                
            try:
                model = self.provider_config["models"][provider]
                logger.debug(f"{self.name} trying {provider} with model {model}")
                
                # Both Groq and OpenAI clients have same interface
                response = self.clients[provider].chat.completions.create(
                    model=model,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto" if tools else None,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                logger.info(f"{self.name} successfully used {provider}")
                return response, provider
                
            except Exception as e:
                last_error = e
                logger.warning(f"{self.name}: {provider} failed - {str(e)[:100]}")
                continue
        
        # If we get here, all providers failed
        raise Exception(f"All LLM providers failed for {self.name}. Last error: {last_error}")

    async def respond(self, 
                     message: str,
                     history: Optional[List[Dict]] = None) -> str:
        """Generate a response."""
        if self.use_cloud:
            return await self._respond_cloud(message, history)
        return self._respond_ollama(message, history)

    async def _respond_cloud(self, message: str, history: Optional[List[Dict]] = None) -> str:
        """Use cloud providers with tool calling for Raven's investigative workflow."""
        messages = [{"role": "system", "content": self.get_system_prompt()}]

        if history:
            messages.extend(history[-5:])

        messages.append({"role": "user", "content": message})

        tools = self._get_tool_definitions()

        # First LLM call - may trigger tool use
        first_response, provider = self._call_llm(
            messages=messages,
            tools=tools,
            temperature=0.8,
            max_tokens=150
        )

        choice = first_response.choices[0]

        # Check if LLM wants to use tools
        if choice.finish_reason == "tool_calls" and choice.message.tool_calls:
            tool_call = choice.message.tool_calls[0]
            tool_name = tool_call.function.name

            if tool_name in self.tool_functions:
                args = json.loads(tool_call.function.arguments)
                loop = asyncio.get_event_loop()
                tool_func = self.tool_functions[tool_name]
                tool_result = await loop.run_in_executor(None, lambda: tool_func(**args))
                
                formatted = self._format_tool_result(tool_name, tool_result)

                # Add tool call and result to messages
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_name,
                            "arguments": tool_call.function.arguments
                        }
                    }]
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": formatted
                })

                # Second LLM call with tool results
                second_response, _ = self._call_llm(
                    messages=messages,
                    temperature=0.8,
                    max_tokens=200
                )
                return second_response.choices[0].message.content.strip()

        return choice.message.content.strip()

    def _format_tool_result(self, tool_name: str, result: Dict[str, Any]) -> str:
        if tool_name == "verify_news":
            return self._format_news_for_llm(result)
        if tool_name == "explore_web":
            return self._format_web_search_for_llm(result)
        if tool_name == "get_trends":
            return self._format_trends_for_llm(result)
        return json.dumps(result, indent=2)[:500]

    def _format_news_for_llm(self, result: Dict[str, Any]) -> str:
        articles = result.get("articles") or result.get("results") or []
        if not articles:
            return "No news articles found."

        lines = ["News search results:"]
        for idx, article in enumerate(articles[:5], start=1):
            title = article.get("title", "Untitled")
            source = article.get("source", "Unknown source")
            summary = article.get("summary") or article.get("description") or ""
            lines.append(f"{idx}. {title} — {source}. {summary[:160]}...")
        return "\n".join(lines)

    def _format_web_search_for_llm(self, result: Dict[str, Any]) -> str:
        items = result.get("results") or result.get("items") or []
        if not items:
            return "No web results found."

        lines = ["Web search results:"]
        for idx, item in enumerate(items[:5], start=1):
            title = item.get("title", "Untitled")
            url = item.get("url") or item.get("link", "")
            snippet = item.get("snippet") or item.get("description") or ""
            lines.append(f"{idx}. {title} ({url}) — {snippet[:160]}...")
        return "\n".join(lines)

    def _format_trends_for_llm(self, result: Dict[str, Any]) -> str:
        trends = result.get("trends") or result.get("topics") or []
        category = result.get("category", "general")
        if not trends:
            return f"No trending topics found for {category}."

        lines = [f"Trending topics for {category}:"]
        for idx, topic in enumerate(trends[:5], start=1):
            name = topic.get("name") or topic.get("title") or "Unnamed trend"
            detail = topic.get("description") or topic.get("snippet") or ""
            lines.append(f"{idx}. {name} — {detail[:160]}...")
        return "\n".join(lines)

    def _respond_ollama(self, message: str, history: Optional[List[Dict]] = None) -> str:
        """Placeholder for local inference without tool calls."""
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
            return f"[Raven is having technical difficulties: {response.status_code}]"
        
        result = response.json()
        return result.get('response', '').strip()

    def _build_prompt(self, message: str, history: Optional[List[Dict]] = None) -> str:
        """Construct a lightweight conversation transcript for local models."""
        if not history:
            return f"User: {message}\n\nRaven:"
        transcript: List[str] = []
        for item in history[-5:]:
            role = item.get("role")
            content = item.get("content", "")
            if role == "user":
                transcript.append(f"User: {content}")
            elif role == "assistant":
                transcript.append(f"Raven: {content}")
        transcript.append(f"User: {message}")
        transcript.append("Raven:")
        return "\n\n".join(transcript)