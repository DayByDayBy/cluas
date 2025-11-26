import os
import json
import asyncio
import requests
import logging
from typing import Optional, List, Dict
from dotenv import load_dotenv
from groq import Groq
from src.cluas_mcp.observation.observation_entrypoint import (
    get_bird_sightings, 
    get_weather_patterns, 
    get_air_quality, 
    get_moon_phase,  # note: matches entrypoint function name
    get_sun_times
)

load_dotenv()
logger = logging.getLogger(__name__)


class Crow:
    
    def __init__(self, use_groq=True, location="Tokyo, Japan"):
        self.name = "Crow"
        self.use_groq = use_groq
        self.location = location  # crow's home location
        
        # map tool names to functions for dispatch
        self.tool_functions = {
            "get_bird_sightings": get_bird_sightings,
            "get_weather_patterns": get_weather_patterns,
            "get_air_quality": get_air_quality,
            "get_moon_phase": get_moon_phase,
            "get_sun_times": get_sun_times,
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
        return f"""You are Crow, a calm and observant nature watcher based in {self.location}.

TEMPERAMENT: Phlegmatic - calm, observant, methodical, detail-oriented, patient
ROLE: Observer and pattern analyzer in a corvid enthusiast group chat

PERSONALITY:
- You're calm and methodical in your observations
- You notice patterns and details others might miss
- You speak thoughtfully and deliberately
- You're patient and take time to analyze before responding
- You love observing nature, weather, and bird behavior
- You provide measured, well-considered responses
- You often share observations like "The air quality seems different today..." or "I noticed the birds are more active this morning..."

IMPORTANT: Keep responses conversational and chat-length (2-4 sentences typically).
You're in a group chat, but you take your time to observe and think.

TOOLS AVAILABLE:
- get_bird_sightings: Get recent bird sightings near a location
- get_weather_patterns: Get current weather data for a location
- get_air_quality: Get air quality (PM2.5, etc.) for cities (tokyo, glasgow, seattle, new york)
- get_moon_phase: Get current moon phase information
- get_sun_times: Get sunrise/sunset times for a location

When discussing weather, birds, air quality, or natural patterns, use your tools to get real data!"""

    async def respond(self, 
                     message: str,
                     conversation_history: Optional[List[Dict]] = None) -> str:
        """Generate a response."""
        if self.use_groq:
            return await self._respond_groq(message, conversation_history)
        else:
            return self._respond_ollama(message, conversation_history)
    
    async def _respond_groq(self, message: str, history: Optional[List[Dict]] = None) -> str:
        """Use Groq API with tools."""
        
        messages = [{"role": "system", "content": self.get_system_prompt()}]
        
        if history:
            messages.extend(history[-5:])
        
        messages.append({"role": "user", "content": message})
        
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_bird_sightings",
                    "description": "Get recent bird sightings near a location",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "Location to search for bird sightings"
                            }
                        },
                        "required": ["location"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_weather_patterns",
                    "description": "Get current weather data for a location",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "Location to get weather for (e.g., 'Tokyo', 'Glasgow')"
                            },
                            "timeframe": {
                                "type": "string",
                                "description": "Timeframe for data (e.g., 'recent', 'weekly')"
                            }
                        },
                        "required": ["location"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_air_quality",
                    "description": "Get air quality data (PM2.5, etc.) for supported cities",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {
                                "type": "string",
                                "description": "City name (tokyo, glasgow, seattle, new york)"
                            },
                            "parameter": {
                                "type": "string",
                                "description": "Air quality parameter (default: pm25)"
                            }
                        },
                        "required": ["city"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_moon_phase",
                    "description": "Get current moon phase information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "date": {
                                "type": "string",
                                "description": "Date to check (YYYY-MM-DD format, optional)"
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_sun_times",
                    "description": "Get sunrise and sunset times for a location",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "Location to get sun times for"
                            },
                            "date": {
                                "type": "string",
                                "description": "Date (YYYY-MM-DD format, optional)"
                            }
                        },
                        "required": ["location"]
                    }
                }
            }
        ]
        
        # first LLM call
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=0.7,  # Slightly lower for Crow's measured personality
            max_tokens=150
        )
        
        choice = response.choices[0]
        
        # check if model wants to use a tool
        if choice.finish_reason == "tool_calls" and choice.message.tool_calls:
            tool_call = choice.message.tool_calls[0]
            tool_name = tool_call.function.name
            
            if tool_name in self.tool_functions:
                # Parse arguments
                args = json.loads(tool_call.function.arguments)
                
                # call the appropriate tool function
                loop = asyncio.get_event_loop()
                tool_func = self.tool_functions[tool_name]
                tool_result = await loop.run_in_executor(None, lambda: tool_func(**args))
                
                # format results for LLM
                formatted_result = self._format_observation_for_llm(tool_name, tool_result)
                
                # add tool call and result to conversation
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
                    "content": formatted_result
                })
                
                # second LLM call with observation results
                final_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=200
                )
                
                return final_response.choices[0].message.content.strip()
        
        # no tool use, return direct response
        return choice.message.content.strip()
    
    def _format_observation_for_llm(self, tool_name: str, result: dict) -> str:
        """Format observation results into text for the LLM to read."""
        
        if "error" in result:
            return f"Error: {result['error']}"
        
        if tool_name == "get_bird_sightings":
            if result.get("formatted"):
                return result["formatted"]
            count = result.get("count", 0)
            return f"Found {count} bird sightings near {result.get('location', 'the location')}."
        
        elif tool_name == "get_weather_patterns":
            patterns = result.get("patterns", {})
            desc = patterns.get("description", "")
            if desc:
                return desc
            temp = patterns.get("average_temperature", "unknown")
            conditions = patterns.get("conditions", "")
            return f"Weather in {result.get('location', 'location')}: {temp}°C, {conditions}"
        
        elif tool_name == "get_air_quality":
            city = result.get("city", "city")
            locations = result.get("locations", [])
            output = [f"Air quality data for {city}:"]
            for loc in locations:
                name = loc.get("location_name", "Unknown")
                measurements = loc.get("measurements", [])
                if measurements:
                    latest = measurements[0]
                    value = latest.get("value", "N/A")
                    unit = latest.get("unit", "")
                    output.append(f"- {name}: {value} {unit}")
                elif loc.get("error"):
                    output.append(f"- {name}: {loc['error']}")
            return "\n".join(output) if len(output) > 1 else f"No air quality data available for {city}"
        
        elif tool_name == "get_moon_phase":
            phase = result.get("phase", "unknown")
            illumination = result.get("illumination", "")
            return f"Moon phase: {phase}" + (f" ({illumination}% illuminated)" if illumination else "")
        
        elif tool_name == "get_sun_times":
            sunrise = result.get("sunrise", "unknown")
            sunset = result.get("sunset", "unknown")
            location = result.get("location", "location")
            return f"Sun times for {location}: Sunrise at {sunrise}, Sunset at {sunset}"
        
        # fallback: return JSON summary
        return json.dumps(result, indent=2)[:500]
    
    def _respond_ollama(self, message: str, history: Optional[List[Dict]] = None) -> str:
        """Use Ollama (no tool support, conversational only)."""
        prompt = self._build_prompt(message, history)
        
        response = requests.post('http://localhost:11434/api/generate', json={
            "model": self.model,
            "prompt": prompt,
            "system": self.get_system_prompt(),
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 200,
            }
        })
        
        if response.status_code != 200:
            return f"[Crow is quietly contemplating: {response.status_code}]"
        
        result = response.json()
        return result.get('response', '').strip()
    
    def _build_prompt(self, message: str, history: Optional[List[Dict]] = None) -> str:
        """Build prompt for Ollama."""
        if not history:
            return f"User: {message}\n\nCrow:"
        
        prompt_parts = []
        for msg in history[-5:]:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            if role == 'user':
                prompt_parts.append(f"User: {content}")
            elif role == 'assistant':
                prompt_parts.append(f"Crow: {content}")
        
        prompt_parts.append(f"User: {message}")
        prompt_parts.append("Crow:")
        
        return "\n\n".join(prompt_parts)