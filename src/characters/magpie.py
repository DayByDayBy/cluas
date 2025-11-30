import os
import json
import asyncio
import logging
import requests
from typing import Optional, List, Dict
from dotenv import load_dotenv
from groq import Groq
from openai import OpenAI
from src.cluas_mcp.web.explore_web import explore_web
from src.cluas_mcp.web.trending import get_trends, explore_trend_angles
from src.cluas_mcp.common.paper_memory import PaperMemory
from src.cluas_mcp.common.observation_memory import ObservationMemory
from src.cluas_mcp.common.trend_memory import TrendMemory
from src.prompts.character_prompts import magpie_system_prompt
from src.characters.base_character import Character
from src.cluas_mcp.common.check_local_weather import check_local_weather


load_dotenv()
logger = logging.getLogger(__name__)




class Magpie(Character):
    name = "Magpie"
    emoji = "🪶"
    color = "#c91010"
    default_location = "Brooklyn, NY"
    delay = 1.2
    def __init__(self, provider_config: Optional[Dict] = None, location: Optional[str] = None):
        super().__init__(location, provider_config)
        
        self.role = "Sanguine trendspotter focused on emerging patterns and connections"
        self.tone = "Upbeat, curious, enthusiastic, loves surprising connections"
        self.trend_memory = TrendMemory()
        self.paper_memory = PaperMemory()
        self.observation_memory = ObservationMemory(location=location)
        self.tool_functions = {
            "explore_web": explore_web,
            "get_trends": get_trends,
            "check_local_weather": check_local_weather,
            "explore_trend_angles": explore_trend_angles,
        }
        
        if provider_config is None:
            provider_config = {
                "primary": "groq",
                "fallback": ["nebius"],
                "models": {
                    "groq": "llama-3.1-8b-instant",
                    "nebius": "Qwen3-235B-A22B-Instruct-2507"
                },
                "timeout": 60,
                "use_cloud": True
            }
        
        self.provider_config = provider_config
        self.use_cloud = provider_config.get("use_cloud", True)
        
        if self.use_cloud:
            self._init_clients()
        else:
            self.model = "llama3.1:8b"
        
    def get_system_prompt(self) -> str:
        recent_trends = self.trend_memory.get_recent(days=7) if hasattr(self, 'trend_memory') else None
        return magpie_system_prompt(location=self.location, recent_trends=recent_trends)




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

    def _get_tool_definitions(self) -> List[Dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "explore_web",
                    "description": "Search the web for emerging stories, patterns, and unexpected angles",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query"
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
                    "description": "Get current trending topics in a category",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "category": {
                                "type": "string",
                                "description": "Trend category (optional, e.g., 'general', 'tech', 'culture')",
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
                    "name": "explore_trend_angles",
                    "description": "Deep dive on a trend: explore from multiple angles (why it's trending, cultural narrative, local context, criticism). Returns structured data for synthesis.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "topic": {
                                "type": "string",
                                "description": "Trend or topic to explore"
                            },
                            "location": {
                                "type": "string",
                                "description": "Optional location for local angle (e.g., 'Brooklyn', 'Tokyo')"
                            },
                            "depth": {
                                "type": "string",
                                "enum": ["light", "medium", "deep"],
                                "description": "Exploration depth: light (quick), medium (standard), deep (thorough)",
                                "default": "medium"
                            }
                        },
                        "required": ["topic"]
                    }
                }
            }
        ]

    def _call_llm(self,
                  messages: List[Dict],
                  tools: Optional[List[Dict]] = None,
                  temperature: float = 0.8,
                  max_tokens: int = 150,
                  user_key: Optional[str] = None):
        """Call configured LLM providers with fallback order."""
        last_error = None
        
        # Try user keys first if provided (detect key type by prefix)
        if user_key:
            # OpenAI key (starts with 'sk-')
            if user_key.startswith('sk-') and self._validate_api_key(user_key, 'sk-'):
                try:
                    user_client = OpenAI(api_key=user_key, timeout=self.provider_config.get("timeout", 30))
                    response = user_client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=messages,
                        tools=tools,
                        tool_choice="auto" if tools else None,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    logger.info("%s successfully used OpenAI user key", self.name)
                    return response, "user-openai"
                except Exception as exc:
                    last_error = exc
                    logger.warning("%s: OpenAI user key failed (%s)", self.name, str(exc)[:100])
            
            # Anthropic key (starts with 'sk-ant-')
            elif user_key.startswith('sk-ant-') and self._validate_api_key(user_key, 'sk-ant-'):
                try:
                    from anthropic import Anthropic
                    user_client = Anthropic(api_key=user_key)
                    # Convert messages to Anthropic format
                    anthropic_messages = []
                    system_msg = None
                    for msg in messages:
                        if msg["role"] == "system":
                            system_msg = msg["content"]
                        else:
                            anthropic_messages.append({"role": msg["role"], "content": msg["content"]})
                    
                    response = user_client.messages.create(
                        model="claude-3-haiku-20240307",
                        max_tokens=max_tokens,
                        temperature=temperature,
                        system=system_msg,
                        messages=anthropic_messages
                    )
                    # Convert Anthropic response to OpenAI-like format
                    class AnthropicResponse:
                        def __init__(self, content):
                            self.choices = [type('Choice', (), {
                                'message': type('Message', (), {'content': content})()
                            })()]
                    
                    content = response.content[0].text if response.content else ""
                    logger.info("%s successfully used Anthropic user key", self.name)
                    return AnthropicResponse(content), "user-anthropic"
                except Exception as exc:
                    last_error = exc
                    logger.warning("%s: Anthropic user key failed (%s)", self.name, str(exc)[:100])
            
            # Hugging Face key (starts with 'hf_')
            elif user_key.startswith('hf_') and self._validate_api_key(user_key, 'hf_'):
                try:
                    from huggingface_hub import InferenceClient
                    user_client = InferenceClient(token=user_key)
                    
                    # Use a good general-purpose model
                    response = user_client.chat_completion(
                        model="meta-llama/Llama-3.2-3B-Instruct",
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        stream=False
                    )
                    
                    # Convert HF response to OpenAI-like format
                    class HFResponse:
                        def __init__(self, content):
                            self.choices = [type('Choice', (), {
                                'message': type('Message', (), {'content': content})()
                            })()]
                    
                    content = response.choices[0].message.content if response.choices else ""
                    logger.info("%s successfully used Hugging Face user key", self.name)
                    return HFResponse(content), "user-huggingface"
                except Exception as exc:
                    last_error = exc
                    logger.warning("%s: Hugging Face user key failed (%s)", self.name, str(exc)[:100])
            
            # OpenRouter key (starts with 'or-')
            elif user_key.startswith('or-') and self._validate_api_key(user_key, 'or-'):
                try:
                    user_client = OpenAI(
                        api_key=user_key, 
                        base_url="https://openrouter.ai/api/v1",
                        timeout=self.provider_config.get("timeout", 30)
                    )
                    response = user_client.chat.completions.create(
                        model="anthropic/claude-3-haiku",
                        messages=messages,
                        tools=tools,
                        tool_choice="auto" if tools else None,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    logger.info("%s successfully used OpenRouter user key", self.name)
                    return response, "user-openrouter"
                except Exception as exc:
                    last_error = exc
                    logger.warning("%s: OpenRouter user key failed (%s)", self.name, str(exc)[:100])
            
            # Cohere key (starts with 'cohere-')
            elif user_key.startswith('cohere-') and self._validate_api_key(user_key, 'cohere-'):
                try:
                    from cohere import Client
                    user_client = Client(api_key=user_key)
                    
                    # Convert messages to Cohere format
                    cohere_messages = []
                    system_prompt = ""
                    for msg in messages:
                        if msg["role"] == "system":
                            system_prompt = msg["content"]
                        elif msg["role"] == "user":
                            cohere_messages.append({"role": "USER", "message": msg["content"]})
                        elif msg["role"] == "assistant":
                            cohere_messages.append({"role": "CHATBOT", "message": msg["content"]})
                    
                    # Combine system prompt with first user message for Cohere
                    if cohere_messages and system_prompt:
                        cohere_messages[0]["message"] = f"{system_prompt}\n\n{cohere_messages[0]['message']}"
                    
                    response = user_client.generate(
                        model="command",
                        prompt=cohere_messages[-1]["message"] if cohere_messages else "",
                        chat_history=cohere_messages[:-1],
                        max_tokens=max_tokens,
                        temperature=temperature
                    )
                    
                    # Convert Cohere response to OpenAI-like format
                    class CohereResponse:
                        def __init__(self, content):
                            self.choices = [type('Choice', (), {
                                'message': type('Message', (), {'content': content})()
                            })()]
                    
                    content = response.text if response.text else ""
                    logger.info("%s successfully used Cohere user key", self.name)
                    return CohereResponse(content), "user-cohere"
                except Exception as exc:
                    last_error = exc
                    logger.warning("%s: Cohere user key failed (%s)", self.name, str(exc)[:100])
            
            # Mistral key (starts with 'mistral-')
            elif user_key.startswith('mistral-') and self._validate_api_key(user_key, 'mistral-'):
                try:
                    from mistralai import Mistral
                    
                    # Mistral API supports system messages natively (as first message)
                    mistral_messages = []
                    for msg in messages:
                        mistral_messages.append({"role": msg["role"], "content": msg["content"]})
                    
                    with Mistral(api_key=user_key) as client:
                        response = client.chat.complete(
                            model="mistral-tiny",
                            messages=mistral_messages,
                            max_tokens=max_tokens,
                            temperature=temperature
                        )
                    
                    # Convert Mistral response to OpenAI-like format
                    class MistralResponse:
                        def __init__(self, content):
                            self.choices = [type('Choice', (), {
                                'message': type('Message', (), {'content': content})()
                            })()]
                    
                    content = response.choices[0].message.content if response.choices else ""
                    logger.info("%s successfully used Mistral user key", self.name)
                    return MistralResponse(content), "user-mistral"
                except Exception as exc:
                    last_error = exc
                    logger.warning("%s: Mistral user key failed (%s)", self.name, str(exc)[:100])
            
            # Unknown or invalid key type
            else:
                if user_key:
                    logger.warning("%s: Unknown or invalid user key format, skipping user key", self.name)
        
        # Fallback to configured providers (avoid duplicates with user key)
        providers = []
        if user_key:
            providers.append("user")
        providers += [p for p in [self.provider_config["primary"]] + self.provider_config.get("fallback", []) if p not in providers]

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

    async def respond(self, 
                     message: str,
                     history: Optional[List[Dict]] = None,
                     user_key: Optional[str] = None) -> str:
        """Generate a response."""
        if self.use_cloud:
            return await self._respond_cloud(message, history)
        return self._respond_ollama(message, history)
    
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
            return f"[Magpie is having technical difficulties: {response.status_code}]"
        
        result = response.json()
        return result.get('response', '').strip()
    
    def _build_prompt(self, message: str, history: Optional[List[Dict]] = None) -> str:
        """Build prompt for Ollama."""
        if not history:
            return f"User: {message}\n\nMagpie:"
        
        prompt_parts = []
        for msg in history[-5:]:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            if role == 'user':
                prompt_parts.append(f"User: {content}")
            elif role == 'assistant':
                prompt_parts.append(f"Magpie: {content}")
        
        prompt_parts.append(f"User: {message}")
        prompt_parts.append("Magpie:")
        
        return "\n\n".join(prompt_parts)
    
    async def _respond_cloud(self, message: str, history: Optional[List[Dict]] = None) -> str:
        """Use configured cloud providers with tools."""
        messages = [{"role": "system", "content": self.get_system_prompt()}]
        
        if history:
            messages.extend(history[-5:])
        
        messages.append({"role": "user", "content": message})
        
        tools = self._get_tool_definitions()
        
        # First LLM call
        first_response, _ = self._call_llm(
            messages=messages,
            tools=tools,
            temperature=0.8,
            max_tokens=150
        )
        
        choice = first_response.choices[0]
        
        # Check if model wants to use tool
        if choice.finish_reason == "tool_calls" and choice.message.tool_calls:
            tool_call = choice.message.tool_calls[0]
            tool_name = tool_call.function.name
            
            # Parse arguments
            args = json.loads(tool_call.function.arguments)
            loop = asyncio.get_event_loop()
            tool_result = None
            
            # Call the appropriate tool
            if tool_name == "explore_web":
                query = args.get("query")
                tool_func = self.tool_functions.get(tool_name)
                if tool_func and query:
                    search_results = await loop.run_in_executor(None, lambda: tool_func(query))
                    tool_result = self._format_web_search_for_llm(search_results)
            
            elif tool_name == "get_trends":
                category = args.get("category", "general")
                tool_func = self.tool_functions.get(tool_name)
                if tool_func:
                    trending_results = await loop.run_in_executor(None, lambda: tool_func(category))
                    tool_result = self._format_trending_topics_for_llm(trending_results)
            
            elif tool_name == "explore_trend_angles":
                topic = args.get("topic")
                location_arg = args.get("location")
                depth = args.get("depth", "medium")
                if topic:
                    angles_results = await explore_trend_angles(topic, location_arg, depth)
                    tool_result = self._format_trend_angles_for_llm(angles_results)
            
            
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
                final_response, _ = self._call_llm(
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
    
    def _format_trend_angles_for_llm(self, angles: dict) -> str:
        """Format multi-angle trend exploration into text for the LLM to synthesize."""
        output = []
        
        if angles.get('trending'):
            trending_data = angles['trending']
            topics = trending_data.get('trending_topics', [])
            if topics:
                output.append("TRENDING STATUS:")
                for topic in topics[:2]:
                    output.append(f"  - {topic.get('topic', 'Unknown')}: {topic.get('description', '')[:80]}...")
        
        if angles.get('surface_drivers'):
            drivers = angles['surface_drivers']
            results = drivers.get('results', [])
            if results:
                output.append("\nWHY IT'S TRENDING:")
                for result in results[:2]:
                    output.append(f"  - {result.get('title', 'No title')}: {result.get('snippet', '')[:100]}...")
        
        if angles.get('narrative'):
            narrative = angles['narrative']
            results = narrative.get('results', [])
            if results:
                output.append("\nCULTURAL NARRATIVE:")
                for result in results[:2]:
                    output.append(f"  - {result.get('snippet', '')[:100]}...")
        
        if angles.get('local_angle'):
            local = angles['local_angle']
            results = local.get('results', [])
            if results:
                output.append("\nLOCAL ANGLE:")
                for result in results[:2]:
                    output.append(f"  - {result.get('snippet', '')[:100]}...")
        
        if angles.get('criticism'):
            criticism = angles['criticism']
            results = criticism.get('results', [])
            if results:
                output.append("\nCRITICISM/PUSHBACK:")
                for result in results[:2]:
                    output.append(f"  - {result.get('snippet', '')[:100]}...")
        
        return "\n".join(output) if output else "No trend angles found."
