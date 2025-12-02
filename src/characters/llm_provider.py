"""
Shared LLM provider implementation for all characters.
Eliminates code duplication across character classes.
"""
import os
import logging
from typing import Dict, List, Optional, Tuple, Any
from groq import Groq
from openai import OpenAI

logger = logging.getLogger(__name__)


class LLMResponse:
    """Wrapper to normalize responses from different providers to OpenAI-like format."""
    def __init__(self, content: str, tool_calls: Optional[List[Dict]] = None):
        self.choices = [type('Choice', (), {
            'message': type('Message', (), {
                'content': content,
                'tool_calls': tool_calls or []
            })(),
            'finish_reason': 'tool_calls' if tool_calls else 'stop'
        })()]


class LLMProvider:
    """Centralized LLM provider with support for multiple backends and user keys."""
    
    def __init__(self, name: str, provider_config: Dict, clients: Dict):
        """
        Initialize LLM provider.
        
        Args:
            name: Character name for logging
            provider_config: Provider configuration dict
            clients: Pre-initialized client dict (from _init_clients)
        """
        self.name = name
        self.provider_config = provider_config
        self.clients = clients
    
    def _validate_api_key(self, key: str, expected_prefix: str) -> bool:
        """Validate API key format and safety."""
        if not key or len(key) < 20 or len(key) > 200:
            return False
        if not key.startswith(expected_prefix):
            return False
        # Only allow alphanumeric, dash, underscore
        return all(c.isalnum() or c in '-_' for c in key)
    
    def call_llm(
        self,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None,
        temperature: float = 0.8,
        max_tokens: int = 150,
        user_key: Optional[str] = None
    ) -> Tuple[Any, str]:
        """
        Call configured LLM providers with fallback order.
        
        Returns:
            Tuple of (response_object, provider_name)
        """
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
                    content = response.content[0].text if response.content else ""
                    logger.info("%s successfully used Anthropic user key", self.name)
                    return LLMResponse(content), "user-anthropic"
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
                    
                    content = response.choices[0].message.content if response.choices else ""
                    logger.info("%s successfully used Hugging Face user key", self.name)
                    return LLMResponse(content), "user-huggingface"
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
                    
                    content = response.text if response.text else ""
                    logger.info("%s successfully used Cohere user key", self.name)
                    return LLMResponse(content), "user-cohere"
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
                    
                    content = response.choices[0].message.content if response.choices else ""
                    logger.info("%s successfully used Mistral user key", self.name)
                    return LLMResponse(content), "user-mistral"
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

