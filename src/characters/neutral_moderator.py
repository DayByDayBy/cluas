import os
import logging
from typing import Optional, Dict, List
from dotenv import load_dotenv
from groq import Groq
from openai import OpenAI
from src.characters.base_character import Character

load_dotenv()
logger = logging.getLogger(__name__)

class Moderator(Character):
    """A neutral moderator character for summarizing deliberations."""
    
    name = "Moderator"
    emoji = "⚖️"
    color = "#708090"
    default_location = "Council Chamber"
    role = "Neutral moderator focused on balanced summarization"
    tone = "Neutral, balanced, reasonable, objective"
    delay = 0.5
    
    def __init__(self, location: Optional[str] = None, provider_config: Optional[Dict] = None):
        super().__init__(location, provider_config)
        
        # Optimized config for moderator (summarization only, no tools)
        if provider_config is None:
            provider_config = {
                "primary": "nebius",
                "fallback": ["groq"],
                "models": {
                    "nebius": "Qwen3-30B-A3B-Instruct-2507",  # Quality 85, cost-effective for summaries
                    "groq": "llama-3.1-8b-instant"  # Fallback
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
            logger.warning(f"{self.name}: No LLM provider API keys found, using fallback")
    
    def get_system_prompt(self) -> str:
        """Return a simple system prompt for the moderator."""
        return """You are a neutral moderator. Your role is to summarize discussions in a balanced, objective manner.

TONE: Neutral, balanced, reasonable, objective
PURPOSE: Summarize key points, agreements, and disagreements without taking sides
STYLE: Concise, clear, and fair to all perspectives

Focus on:
- Identifying main arguments from each side
- Highlighting areas of agreement and disagreement
- Maintaining neutrality and balance
- Providing clear, accessible summaries"""
    
    def _call_llm(self, messages: List[Dict], temperature: float = 0.3, max_tokens: int = 300, user_key: Optional[str] = None):
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
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                logger.info("%s successfully used %s", self.name, provider)
                return response, provider
            except Exception as exc:
                last_error = exc
                logger.warning("%s: %s failed (%s)", self.name, provider, str(exc)[:100])
                continue
        
        # Fallback to simple response if all providers fail
        logger.warning(f"All LLM providers failed for {self.name}, using fallback response")
        return None, None
    
    async def respond(self, message: str, history: Optional[List[Dict]] = None, user_key: Optional[str] = None) -> str:
        """Generate a response as the moderator."""
        if self.use_cloud and self.clients:
            return await self._respond_cloud(message, history, user_key)
        return self._respond_fallback(message)
    
    async def _respond_cloud(self, message: str, history: Optional[List[Dict]] = None, user_key: Optional[str] = None) -> str:
        """Use configured cloud providers."""
        messages = [{"role": "system", "content": self.get_system_prompt()}]
        
        if history:
            messages.extend(history[-3:])  # Keep recent context
        
        messages.append({"role": "user", "content": message})
        
        response, provider = self._call_llm(
            messages=messages,
            temperature=0.3,  # Lower temperature for consistency
            max_tokens=300,
            user_key=user_key
        )
        
        if response:
            return response.choices[0].message.content.strip()
        else:
            return self._respond_fallback(message)
    
    def _respond_fallback(self, message: str) -> str:
        """Simple fallback response when LLM providers are unavailable."""
        # Basic summarization logic
        words = message.split()
        if len(words) > 50:
            summary = " ".join(words[:47]) + "..."
            return f"Moderator Summary: {summary}"
        else:
            return f"Moderator Summary: {message}"