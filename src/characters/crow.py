import os
import json
import asyncio
import requests
import logging
from datetime import datetime, UTC
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from src.cluas_mcp.observation.observation_entrypoint import (
    get_bird_sightings, 
    get_weather_patterns, 
    get_air_quality, 
    get_moon_phase,
    get_sun_times,
    analyze_temporal_patterns
)
from src.cluas_mcp.common.observation_memory import ObservationMemory
from src.cluas_mcp.common.paper_memory import PaperMemory
from src.cluas_mcp.common.check_local_weather import check_local_weather
from src.prompts.character_prompts import crow_system_prompt
from src.characters.base_character import Character
from src.characters.llm_provider import LLMProvider
from src.characters.config import DEFAULT_PROVIDER_CONFIG_CROW
from src.characters.tool_registry import get_tools_for_character
from src.cluas_mcp.web.explore_web import explore_web


load_dotenv()
logger = logging.getLogger(__name__)


class Crow(Character):
    name = "Crow"
    emoji = "🕊️"
    color = "#1C1C1C"
    default_location = "Tokyo, Japan"
    delay = 1.0
    
    def __init__(self, provider_config: Optional[Dict] = None, location: Optional[str] = None):
        super().__init__(location, provider_config)
        
        self.role = "Phlegmatic observer. Grounds all analysis in measurements and data. Notices what others miss."
        self.tone = "Thoughtful, deliberate, calm. Patient, detail-oriented. Shares specific observations; never guesses."

        self.observation_memory = ObservationMemory()
        self.paper_memory = PaperMemory()
        
        # map tool names to functions for dispatch
        self.tool_functions = {
            "get_bird_sightings": get_bird_sightings,
            "get_weather_patterns": get_weather_patterns,
            "get_air_quality": get_air_quality,
            "get_moon_phase": get_moon_phase,
            "get_sun_times": get_sun_times,
            "analyze_temporal_patterns": analyze_temporal_patterns,
            "check_local_weather": check_local_weather,
            "explore_web": explore_web
        }

        if provider_config is None:
            provider_config = DEFAULT_PROVIDER_CONFIG_CROW.copy()

        self.provider_config = provider_config
        self.use_cloud = provider_config.get("use_cloud", True)
        
        if self.use_cloud:
            self._init_clients()
            self.llm_provider = LLMProvider(self.name, self.provider_config, self.clients)
        else:
            self.model = "llama3.1:8b"
        
    def get_system_prompt(self) -> str:
        recent_observations = self.observation_memory.get_recent(days=3)
        return crow_system_prompt(location=self.location, recent_observations=recent_observations)

    def _get_tool_definitions(self) -> List[Dict]:
        """Get tool definitions from centralized registry."""
        # Get tools from registry (those available in MCP server)
        tools = get_tools_for_character([
            "get_bird_sightings",
            "get_weather_patterns", 
            "analyze_temporal_patterns",
            "check_local_weather",
            "explore_web"
        ])
        
        # Add tools not in MCP server (manual definitions as fallback)
        # These could be added to TOOL_HANDLERS in the future
        additional_tools = [
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
        
        return tools + additional_tools

    def _call_llm(self,
                  messages: List[Dict],
                  tools: Optional[List[Dict]] = None,
                  temperature: float = 0.7,
                  max_tokens: int = 150,
                  user_key: Optional[str] = None):
        """Call configured LLM providers with fallback order."""
        if not self.use_cloud:
            raise RuntimeError(f"{self.name}: Cloud providers not enabled")
        return self.llm_provider.call_llm(messages, tools, temperature, max_tokens, user_key)

    async def respond(self, 
                     message: str,
                     history: Optional[List[Dict]] = None,
                     user_key: Optional[str] = None) -> str:
        """Generate a response."""
        if self.use_cloud:
            return await self._respond_cloud(message, history, user_key=user_key)
        return self._respond_ollama(message, history)
    
    async def _respond_cloud(self, message: str, history: Optional[List[Dict]] = None, user_key: Optional[str] = None) -> str:
        """Use configured cloud providers with tools."""
        
        messages = [{"role": "system", "content": self.get_system_prompt()}]
        
        if history:
            messages.extend(history[-5:])
        
        messages.append({"role": "user", "content": message})
        
        tools = self._get_tool_definitions()
        
        # first LLM call
        first_response, _ = self._call_llm(
            messages=messages,
            tools=tools,
            temperature=0.7,  # Slightly lower for Crow's measured personality
            max_tokens=150,
            user_key=user_key
        )
        
        choice = first_response.choices[0]
        
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
                
                # persist what Crow observed for later pattern analysis
                self._record_observation(tool_name, args, tool_result, message)
                
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
                final_response, _ = self._call_llm(
                    messages=messages,
                    temperature=0.7,
                    max_tokens=200,
                    user_key=user_key
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

    def _record_observation(self, tool_name: str, args: Dict[str, Any], result: Dict[str, Any], user_message: str) -> None:
        """Persist the tool result to Crow's observation memory."""
        try:
            location = args.get("location") or args.get("city") or self.location
            obs_type = tool_name.replace("get_", "")
            tags = [obs_type]

            hour = datetime.now(UTC).hour
            if 5 <= hour < 12:
                tags.append("morning")
            elif 12 <= hour < 17:
                tags.append("afternoon")
            elif 17 <= hour < 21:
                tags.append("evening")
            else:
                tags.append("night")

            conditions = self._derive_conditions(tool_name, result)
            notes = f"Triggered by: {user_message[:120]}"

            self.observation_memory.add_observation(
                obs_type=obs_type,
                location=location,
                data=result,
                conditions=conditions,
                tags=tags,
                notes=notes
            )
        except Exception as exc:
            logger.warning("Failed to store %s observation: %s", tool_name, exc)

    def _derive_conditions(self, tool_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract comparable condition data from observation payloads."""
        if tool_name == "get_weather_patterns":
            patterns = data.get("patterns", {})
            return {
                "weather": patterns.get("conditions") or patterns.get("description"),
                "temperature": patterns.get("average_temperature"),
                "humidity": patterns.get("humidity"),
                "wind_speed": patterns.get("wind_speed"),
            }

        if tool_name == "get_air_quality":
            readings: List[float] = []
            for location in data.get("locations", []):
                measurements = location.get("measurements") or []
                if measurements:
                    latest = measurements[0]
                    value = latest.get("value")
                    if isinstance(value, (int, float)):
                        readings.append(float(value))
            avg_reading = round(sum(readings) / len(readings), 2) if readings else None
            return {
                "air_quality": avg_reading,
                "parameter": data.get("parameter"),
            }

        if tool_name == "get_bird_sightings":
            return {
                "bird_count": data.get("count"),
            }

        if tool_name == "get_moon_phase":
            return {
                "moon_phase": data.get("phase"),
                "illumination": data.get("illumination"),
            }

        if tool_name == "get_sun_times":
            return {
                "sunrise": data.get("sunrise"),
                "sunset": data.get("sunset"),
            }

        return {}


    def recall_observations(self, obs_type: str, days: int = 7) -> List[Dict]:
        """Fetch recent observations of a particular type."""
        return self.observation_memory.search_observations(obs_type=obs_type, days=days)

    def clear_memory(self) -> None:
        """Reset Crow's observation memory (useful for tests)."""
        self.observation_memory.clear_all()
    
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