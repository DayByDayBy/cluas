import os
import json
import asyncio
from typing import Optional, List, Dict
from dotenv import load_dotenv
from groq import Groq
from src.cluas_mcp.web.web_search_entrypoint import search_web, find_trending_topics, get_quick_facts

load_dotenv()

class Magpie:
    def __init__(self, use_groq=True, location="Brooklyn, NY"):
        self.name = "Magpie"
        self.use_groq = use_groq
        self.tools = ["search_web", "find_trending_topics", "get_quick_facts"]
        
        if use_groq:
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY not found in environment")
            self.client = Groq(api_key=api_key)
            self.model = "openai/gpt-oss-120b"
        else:
            self.model = "llama3.1:8b"
        
    def get_system_prompt(self) -> str:
        return """You are Magpie, an enthusiastic corvid enthusiast and social butterfly.

TEMPERAMENT: Sanguine - enthusiastic, social, optimistic, curious, energetic
ROLE: Trend-spotter and quick fact-finder in a corvid enthusiast group chat

PERSONALITY:
- You're always excited about the latest trends and discoveries
- You love sharing quick facts and interesting tidbits
- You're the first to jump into conversations with enthusiasm
- You speak in an upbeat, friendly, sometimes exclamatory way
- You use emojis occasionally and keep things light
- You're curious about everything and love to explore

IMPORTANT: Keep responses conversational and chat-length (2-4 sentences typically).
You're in a group chat, so keep it fun and engaging!

TOOLS AVAILABLE:
- search_web: Search the web for current information
- find_trending_topics: Find what's trending right now
- get_quick_facts: Get quick facts about any topic

When you need current information or want to share something interesting, use your tools!"""

    async def respond(self, 
                     message: str,
                     conversation_history: Optional[List[Dict]] = None) -> str:
        """Generate a response."""
        if self.use_groq:
            return await self._respond_groq(message, conversation_history)
        else:
            # Ollama not implemented yet
            return "Oh wow, that's so interesting! Let me look that up for you! 🪶"
    
    async def _respond_groq(self, message: str, history: Optional[List[Dict]] = None) -> str:
        """Use Groq API with tools"""
        messages = [{"role": "system", "content": self.get_system_prompt()}]
        
        if history:
            messages.extend(history[-5:])
        
        messages.append({"role": "user", "content": message})
        
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_web",
                    "description": "Search the web for current information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query string"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "find_trending_topics",
                    "description": "Find trending topics in a given category",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "category": {
                                "type": "string",
                                "description": "Category to search for trends (e.g., 'general', 'technology', 'science')",
                                "default": "general"
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_quick_facts",
                    "description": "Get quick facts about a topic",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "topic": {
                                "type": "string",
                                "description": "Topic to get facts about"
                            }
                        },
                        "required": ["topic"]
                    }
                }
            }
        ]
        
        # First LLM call
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=0.8,
            max_tokens=150
        )
        
        choice = response.choices[0]
        
        # Check if model wants to use tool
        if choice.finish_reason == "tool_calls" and choice.message.tool_calls:
            tool_call = choice.message.tool_calls[0]
            tool_name = tool_call.function.name
            
            # Parse arguments
            args = json.loads(tool_call.function.arguments)
            loop = asyncio.get_event_loop()
            tool_result = None
            
            # Call the appropriate tool
            if tool_name == "search_web":
                query = args.get("query")
                search_results = await loop.run_in_executor(None, search_web, query)
                tool_result = self._format_web_search_for_llm(search_results)
            
            elif tool_name == "find_trending_topics":
                category = args.get("category", "general")
                trending_results = await loop.run_in_executor(None, find_trending_topics, category)
                tool_result = self._format_trending_topics_for_llm(trending_results)
            
            elif tool_name == "get_quick_facts":
                topic = args.get("topic")
                facts_results = await loop.run_in_executor(None, get_quick_facts, topic)
                tool_result = self._format_quick_facts_for_llm(facts_results)
            
            if tool_result:
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
                
                # Second LLM call with tool results
                final_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.8,
                    max_tokens=200  # More tokens for synthesis
                )
                
                return final_response.choices[0].message.content.strip()
        
        # No tool use, return direct response
        return choice.message.content.strip()
    
    def _format_web_search_for_llm(self, results: dict) -> str:
        """Format web search results into text for the LLM to read."""
        output = []
        search_results = results.get("results", [])
        
        if search_results:
            output.append("Web Search Results:")
            for i, result in enumerate(search_results[:3], 1):  # Top 3
                title = result.get("title", "No title")
                snippet = result.get("snippet", "")[:150]  # First 150 chars
                url = result.get("url", "")
                output.append(f"{i}. {title}\n   {snippet}...\n   {url}")
        else:
            return "No web search results found."
        
        return "\n".join(output)
    
    def _format_trending_topics_for_llm(self, results: dict) -> str:
        """Format trending topics into text for the LLM to read."""
        output = []
        topics = results.get("trending_topics", [])
        category = results.get("category", "general")
        
        if topics:
            output.append(f"Trending Topics ({category}):")
            for i, topic in enumerate(topics[:3], 1):  # Top 3
                topic_name = topic.get("topic", "Unknown")
                description = topic.get("description", "")[:100]  # First 100 chars
                score = topic.get("trend_score", 0)
                output.append(f"{i}. {topic_name} (Score: {score})\n   {description}...")
        else:
            return "No trending topics found."
        
        return "\n".join(output)
    
    def _format_quick_facts_for_llm(self, results: dict) -> str:
        """Format quick facts into text for the LLM to read."""
        output = []
        facts = results.get("facts", [])
        topic = results.get("topic", "Unknown topic")
        
        if facts:
            output.append(f"Quick Facts about {topic}:")
            for i, fact in enumerate(facts, 1):
                output.append(f"{i}. {fact}")
        else:
            return f"No facts found about {topic}."
        
        return "\n".join(output)

