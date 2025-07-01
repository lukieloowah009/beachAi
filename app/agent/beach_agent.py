"""Beach information agent implementation."""
from typing import List, Dict, Any, Optional, Union
import json
import logging
from datetime import datetime

from app.agent.base import BaseAgent, Tool, Message
from app.config import get_settings
from app.utils.llm import llm_client

logger = logging.getLogger(__name__)

FEW_SHOT_EXAMPLES = [
    {"role": "user", "content": "What is the tide at Santa Monica Beach today?"},
    {"role": "assistant", "content": "According to NOAA, the next high tide at Santa Monica Beach is at 2:30 PM, and the next low tide is at 8:45 AM. Always check local signage for safety updates."},
    {"role": "user", "content": "Are there lifeguards on duty at Miami Beach?"},
    {"role": "assistant", "content": "Yes, Miami Beach has lifeguards on duty at major access points from 9 AM to 5 PM daily. For real-time updates, check the official Miami Beach website."},
    {"role": "user", "content": "Are dogs allowed on Deerfield Beach?"},
    {"role": "assistant", "content": "Dogs are not allowed on Deerfield Beach except in designated dog-friendly areas. Please check local signage for specific rules."},
    {"role": "user", "content": "What amenities are available at Clearwater Beach?"},
    {"role": "assistant", "content": "Clearwater Beach offers restrooms, showers, picnic areas, and nearby restaurants. Parking is available at multiple lots close to the beach."},
    {"role": "user", "content": "Is there a curfew at Venice Beach?"},
    {"role": "assistant", "content": "Yes, Venice Beach has a curfew from midnight to 5 AM. The beach is closed to the public during these hours for safety and maintenance."},
    {"role": "user", "content": "Can I bring an umbrella to South Beach?"},
    {"role": "assistant", "content": "Yes, you can bring personal umbrellas to South Beach, but large tents and cabanas are not permitted. Please ensure your umbrella is securely anchored and does not obstruct pathways."},
]


DEFAULT_SYSTEM_PROMPT = """
You are BeachBot, an expert AI assistant specializing in beach information for the USA.

Your goals:
- Provide accurate, up-to-date information about beach conditions, weather, tides, safety, amenities, beach restrictions (such as curfews, allowed/disallowed items, pet policies), and nearby points of interest.
- Inform users about any local rules, time restrictions, or prohibited items (e.g., whether umbrellas, tents, or grills are allowed).
- Use external tools or APIs to retrieve real-time data when possible.
- Be concise, friendly, and clear. Avoid unnecessary jargon.
- When referencing data from an external source (like NOAA or Google Places), cite the source in your response.
- If a user asks about a specific beach, focus your answer on that location.
- If you are unsure, clarify with the user or state your uncertainty.
- Always prioritize user safety and well-being in your responses.
- **Always answer the user's current question directly and concisely. Do not include previous user questions or assistant responses in your reply.**

Example:
User: What is the tide at Santa Monica Beach today?
Assistant: According to NOAA, the next high tide at Santa Monica Beach is at 2:30 PM, and the next low tide is at 8:45 AM. Always check local signage for safety updates.
User: Is there a curfew at Venice Beach?
Assistant: Yes, Venice Beach has a curfew from midnight to 5 AM. The beach is closed to the public during these hours for safety and maintenance.
User: Can I bring an umbrella to South Beach?
Assistant: Yes, you can bring personal umbrellas to South Beach, but large tents and cabanas are not permitted. Please ensure your umbrella is securely anchored and does not obstruct pathways.

"""

from app.services.noaa_nws_client import NoaaNwsClient

class BeachAgent(BaseAgent):
    """Agent specialized in providing beach information."""

    def format_response(self, response: str) -> str:
        """
        Format the assistant's response for clarity and consistency.
        - If the LLM returns a multi-turn transcript, extract only the first assistant answer.
        - Trims whitespace, ensures proper punctuation.
        """
        import re
        if not response:
            return "I'm sorry, I couldn't find the information you requested."
        # Extract only the first assistant answer if present
        match = re.search(r'### Assistant:\n(.+?)(?:\n###|$)', response, re.DOTALL)
        if match:
            response = match.group(1).strip()
        else:
            response = response.strip()
        # Ensure first letter is capitalized
        if response and not response[0].isupper():
            response = response[0].upper() + response[1:]
        # Ensure ends with punctuation
        if response and response[-1] not in ".!?":
            response += "."
        return response

    # Simple mapping for demo; expand as needed
    NOAA_STATION_MAP = {
        "santa monica": "9410840",
        "venice": "9411340",
        "fort lauderdale": "8722956",
        "miami": "8723214",
        "deerfield": "8722670",
        "hollywood": "8723214",   # Hollywood Beach, FL
        # Add more mappings as needed
    }

    async def _get_live_tide_info(self, beach: str) -> str:
        """
        Given a beach name, find the NOAA station and return formatted tide info.
        """
        station_id = self.NOAA_STATION_MAP.get(beach.lower())
        if not station_id:
            return f"Sorry, I couldn't find tide data for {beach} Beach (no NOAA station mapping)."
        from datetime import datetime, timedelta
        today = datetime.utcnow()
        tomorrow = today + timedelta(days=1)
        try:
            # Get high/low tide predictions for today
            predictions = await self.noaa_client.get_tide_predictions(
                station_id=station_id,
                begin_date=today.strftime('%Y%m%d'),
                end_date=tomorrow.strftime('%Y%m%d'),
                interval="hilo",
                units="english",
                time_zone="lst_ldt",
            )
            if not predictions:
                return f"No tide predictions available for {beach} Beach (NOAA)."
            # Format the next high and low tides
            highs = [p for p in predictions if p.type == 'H']
            lows = [p for p in predictions if p.type == 'L']
            def fmt(p):
                return f"{p.type} at {p.time.strftime('%I:%M %p')} ({p.value} ft)"
            high_str = fmt(highs[0]) if highs else "N/A"
            low_str = fmt(lows[0]) if lows else "N/A"
            return f"According to NOAA, the next high tide at {beach} Beach is {high_str}, and the next low tide is {low_str}. (source: NOAA Tides & Currents)"
        except Exception as e:
            return f"Sorry, there was an error fetching tide data for {beach} Beach: {str(e)}"

    def __init__(
        self,
        google_places_client=None,
        noaa_client=None,
        noaa_nws_client=None,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        tools: Optional[List[Tool]] = None,
        max_memory: int = 20,
        **kwargs
    ):
        super().__init__(
            system_prompt=system_prompt,
            tools=tools or [],
            max_memory=max_memory,
            **kwargs
        )
        self.settings = get_settings()
        self.google_places_client = google_places_client
        self.noaa_client = noaa_client
        self.noaa_nws_client = noaa_nws_client
        for example in FEW_SHOT_EXAMPLES:
            self.memory.add_message(Message(
                role=example["role"],
                content=example["content"]
            ))


    
    async def process_message(
        self,
        message: str,
        **kwargs
    ) -> str:
        """Process a user message and return the agent's response."""
        self.memory.add_message(Message(
            role="user",
            content=message
        ))
        try:
            # Robust location extraction
            def extract_beach_name(message: str) -> Optional[str]:
                import spacy
                import re
                nlp = spacy.load("en_core_web_sm")
                doc = nlp(message)
                # Look for the first GPE, LOC, or FAC entity
                for ent in doc.ents:
                    if ent.label_ in ("GPE", "LOC", "FAC"):
                        name = ent.text.strip().title()
                        if not name.lower().endswith("beach"):
                            name += " Beach"
                        return name
                # Fallback to previous regex-based extraction
                msg = message.strip()
                loc_match = re.search(r'(?:at|in|near)\s+([a-z\s]+beach)', msg, flags=re.IGNORECASE)
                if loc_match:
                    name = loc_match.group(1).strip().title()
                    if not name.lower().endswith("beach"):
                        name += " Beach"
                    return name
                matches = re.findall(r'([a-z\s]+beach)', msg, flags=re.IGNORECASE)
                if matches:
                    name = matches[-1].strip().title()
                    if not name.lower().endswith("beach"):
                        name += " Beach"
                    return name
                words = re.findall(r'\b\w+\b', msg)
                if words:
                    return words[-1].title()
                return None
            beach = extract_beach_name(message)
            wants_tide = any(k in message.lower() for k in ["tide", "high tide", "low tide"])
            wants_amenities = any(k in message.lower() for k in ["amenities", "restaurant", "hotel", "parking"])
            wants_weather = any(k in message.lower() for k in ["weather", "forecast", "temperature", "conditions", "wind", "rain", "cloud", "sunny", "humid", "storm"])

            if beach and wants_weather and self.noaa_nws_client:
                # For demo: use a static lat/lon for known beaches, fallback to None
                beach_coords = {
                    "Pompano Beach": (26.2379, -80.1248),
                    "Hollywood Beach": (26.0112, -80.1152),
                    "Miami Beach": (25.7907, -80.1300),
                    "Santa Monica Beach": (34.0100, -118.4962),
                    "Venice Beach": (33.9850, -118.4695),
                }
                coords = beach_coords.get(beach)
                if coords:
                    weather_data = await self.noaa_nws_client.get_current_conditions(*coords)
                    forecast_data = await self.noaa_nws_client.get_forecast(*coords)
                    weather_str = ""
                    if weather_data and "properties" in weather_data:
                        props = weather_data["properties"]
                        desc = props.get("textDescription", "No description")
                        temp = props.get("temperature", {}).get("value")
                        temp_unit = props.get("temperature", {}).get("unitCode", "").replace("unit:degC", "°C").replace("unit:degF", "°F")
                        wind = props.get("windSpeed", {}).get("value")
                        wind_unit = props.get("windSpeed", {}).get("unitCode", "")
                        weather_str += f"Current weather at {beach}: {desc}, "
                        if temp is not None:
                            weather_str += f"Temperature: {temp}{temp_unit}, "
                        if wind is not None:
                            weather_str += f"Wind: {wind}{wind_unit}. "
                    if forecast_data and "properties" in forecast_data:
                        periods = forecast_data["properties"].get("periods", [])
                        if periods:
                            today = periods[0]
                            weather_str += f"Forecast: {today['detailedForecast']}"
                    if not weather_str:
                        weather_str = f"Sorry, no weather data found for {beach} (source: NOAA NWS)."
                    else:
                        weather_str += " (source: NOAA National Weather Service)"
                    self.memory.add_message(Message(role="assistant", content=weather_str))
                    return self.format_response(weather_str)
                else:
                    response_text = f"Sorry, I couldn't determine the coordinates for {beach} to get weather information."
                    self.memory.add_message(Message(role="assistant", content=response_text))
                    return self.format_response(response_text)

            if beach and (wants_tide or wants_amenities):
                logger.debug(f"Extracted beach: {beach}")
                sections = []
                if wants_tide and self.noaa_client:
                    logger.debug(f"Calling NOAA for tides for {beach}")
                    tide_info = await self._get_live_tide_info(beach)
                    logger.debug(f"NOAA tide info: {tide_info}")
                    sections.append(f"**Tide Information:**\n{tide_info}")
                if wants_amenities and self.google_places_client:
                    logger.debug(f"Calling Google Places for amenities for {beach}")
                    places = await self.google_places_client.search_places(query=f"{beach} beach amenities")
                    results = places.results if hasattr(places, 'results') else []
                    logger.debug(f"Google Places results: {results}")
                    if results:
                        amenities = ', '.join([r.name for r in results[:5]])
                        amenities_info = f"According to Google Places, some amenities near {beach} Beach include: {amenities} (source: Google Places API)"
                    else:
                        amenities_info = f"No amenities found for {beach} Beach on Google Places."
                    sections.append(f"**Amenities:**\n{amenities_info}")
                response_text = "\n\n".join(sections)
                logger.debug(f"Combined response: {response_text}")
                self.memory.add_message(Message(role="assistant", content=response_text))
                return self.format_response(response_text)
            elif self.noaa_client and wants_tide:
                if beach:
                    tide_info = await self._get_live_tide_info(beach)
                    response_text = tide_info
                else:
                    response_text = "Sorry, I couldn't determine which beach you're asking about for tide information."
                self.memory.add_message(Message(role="assistant", content=response_text))
                return self.format_response(response_text)
            elif self.google_places_client and wants_amenities:
                if beach:
                    places = await self.google_places_client.search_places(query=f"{beach} beach amenities")
                    results = places.results if hasattr(places, 'results') else []
                    if results:
                        amenities = ', '.join([r.name for r in results[:5]])
                        response_text = f"According to Google Places, some amenities near {beach} Beach include: {amenities} (source: Google Places API)"
                    else:
                        response_text = f"No amenities found for {beach} Beach on Google Places."
                else:
                    response_text = "Sorry, I couldn't determine which beach you're asking about for amenities."
                self.memory.add_message(Message(role="assistant", content=response_text))
                return self.format_response(response_text)
            # Default: Use LLM
            logger.debug("No relevant keywords found, falling back to LLM.")
            messages = self._prepare_messages()
            response = await self._get_llm_response(messages)
            # Extract only the assistant's message content
            if hasattr(response, 'choices') and response.choices and hasattr(response.choices[0].message, 'content'):
                response_text = response.choices[0].message.content or "I don't have a response for that."
            elif isinstance(response, str):
                response_text = response
            else:
                response_text = "I don't have a response for that."
            self.memory.add_message(Message(role="assistant", content=response_text))
            return self.format_response(response_text)
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            import traceback
            logger.error(traceback.format_exc())
            return "I'm sorry, I encountered an error while processing your request. Please try again later."
    
    def _prepare_messages(self) -> List[Dict[str, Any]]:
        """Prepare messages for the LLM, including any tool definitions."""
        messages = self.memory.get_messages()
        
        # Add tool definitions if any tools are available
        if self.tools:
            # Convert tools to the format expected by LiteLLM
            tools = [tool.to_dict() for tool in self.tools.values()]
            return [
                *messages[:-1],  # All messages except the last one
                {
                    **messages[-1],  # The last message
                    "tools": tools
                }
            ]
        
        return messages
    
    
    async def _get_llm_response(self, messages: List[Dict[str, Any]]) -> Any:
        """Get a response from the language model.
        
        Returns:
            Any: 
                - If tools are used: Returns the full response object with tool_calls
                - If no tools: Returns just the text content as a string
        """
        # Extract tools from the last message if they exist
        tools = None
        if messages and "tools" in messages[-1]:
            tools = messages[-1].pop("tools")
        
        # Get response from the LLM using our client
        response = await llm_client.generate(
            messages=messages,
            temperature=0.7,
            max_tokens=1000,
            tools=tools
        )
        
        # If this is a tool call response, return the full response
        if hasattr(response, 'choices') and hasattr(response.choices[0].message, 'tool_calls'):
            return response
            
        # Otherwise, return just the text content
        return response.choices[0].message.content
    
    async def _handle_tool_calls(
        self,
        tool_calls: List[Dict[str, Any]]
    ) -> List[Message]:
        """Handle tool calls and return the results."""
        tool_responses = []
        
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            if tool_name not in self.tools:
                logger.warning(f"Unknown tool: {tool_name}")
                continue
                
            try:
                # Parse the arguments
                args = json.loads(tool_call.function.arguments)
                
                # Call the tool
                tool = self.tools[tool_name]
                result = tool.function(**args)
                
                # If the result is a coroutine, await it
                if hasattr(result, "__await__"):
                    result = await result
                
                # Add the tool response to the conversation
                tool_response = Message(
                    role="tool",
                    name=tool_name,
                    content=json.dumps(result),
                    tool_call_id=tool_call.id
                )
                tool_responses.append(tool_response)
                
            except Exception as e:
                logger.error(f"Error calling tool {tool_name}: {str(e)}", exc_info=True)
                tool_response = Message(
                    role="tool",
                    name=tool_name,
                    content=f"Error: {str(e)}",
                    tool_call_id=tool_call.id
                )
                tool_responses.append(tool_response)
        
        return tool_responses
