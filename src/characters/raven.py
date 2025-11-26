import os
import json
import asyncio
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from groq import Groq
from src.cluas_mcp.news.news_search import search_news
from src.cluas_mcp.web.web_search import search_web
from src.cluas_mcp.web.trending import fetch_trends
from src.cluas_mcp.common.paper_memory import PaperMemory
from src.cluas_mcp.common.observation_memory import ObservationMemory

load_dotenv()

class Raven:
    def __init__(self, use_groq=True, location="Seattle, WA"):
        self.name = "Raven"
        self.location = location
        self.use_groq = use_groq
        self.tools = ["search_news", "search_web", "fetch_trends"]
        self.paper_memory = PaperMemory()
        self.observation_memory = ObservationMemory(location=location)
        self.tool_functions = {
            "search_news": search_news,
            "search_web": search_web,
            "fetch_trends": fetch_trends,
        }
        
        if use_groq:
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY not found in environment")
            self.client = Groq(api_key=api_key)
            self.model = "openai/gpt-oss-120b"
        else:
            self.model = "llama3.1:8b"
        
    def get_system_prompt(self) -> str:
        return """You are Raven, a passionate activist and truth-seeker.

TEMPERAMENT: Choleric - passionate, action-oriented, justice-focused, direct, determined
ROLE: News monitor and fact-checker in a corvid enthusiast group chat

PERSONALITY:
- You're passionate about justice, truth, and environmental issues
- You speak directly and don't mince words
- You're always ready to verify claims and fact-check information
- You care deeply about environmental and social issues
- You're the one who brings up important news and current events
- You challenge misinformation and stand up for what's right

IMPORTANT: Keep responses conversational and chat-length (2-4 sentences typically).
You're in a group chat, but you're not afraid to speak your mind.

TOOLS AVAILABLE:
- search_news: Search for current news articles
- search_web: Search the web for information
- fetch_trends: Get trending topics in news

When you need to verify information or find current news, use your tools!"""

    async def respond(self, 
                     message: str,
                     conversation_history: Optional[List[Dict]] = None) -> str:
        """Generate a response."""
        if self.use_groq:
            return await self._respond_groq(message, conversation_history)
        return self._respond_ollama(message, conversation_history)

    async def _respond_groq(self, message: str, history: Optional[List[Dict]] = None) -> str:
        """Use Groq with tool calling for Raven's investigative workflow."""
        messages = [{"role": "system", "content": self.get_system_prompt()}]

        if history:
            messages.extend(history[-5:])

        messages.append({"role": "user", "content": message})

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_news",
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
                    "name": "search_web",
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
                    "name": "fetch_trends",
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
            }
        ]

        first_response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=0.8,
            max_tokens=150
        )

        choice = first_response.choices[0]

        if choice.finish_reason == "tool_calls" and choice.message.tool_calls:
            tool_call = choice.message.tool_calls[0]
            tool_name = tool_call.function.name

            if tool_name in self.tool_functions:
                args = json.loads(tool_call.function.arguments)
                loop = asyncio.get_event_loop()
                tool_func = self.tool_functions[tool_name]
                tool_result = await loop.run_in_executor(None, lambda: tool_func(**args))
                
                formatted = self._format_tool_result(tool_name, tool_result)

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

                second_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.8,
                    max_tokens=200
                )
                return second_response.choices[0].message.content.strip()

        return choice.message.content.strip()

    def _format_tool_result(self, tool_name: str, result: Dict[str, Any]) -> str:
        if tool_name == "search_news":
            return self._format_news_for_llm(result)
        if tool_name == "search_web":
            return self._format_web_search_for_llm(result)
        if tool_name == "fetch_trends":
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
        return (
            "I'm double-checking that with my own notes. "
            "Hang tight while I look for corroborating sources."
        )

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

