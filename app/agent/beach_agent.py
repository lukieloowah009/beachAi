"""Beach information agent implementation."""
from typing import List, Dict, Any, Optional, Union
import json
import logging
from datetime import datetime

from app.agent.base import BaseAgent, Tool, Message
from app.config import get_settings
from app.utils.llm import llm_client

logger = logging.getLogger(__name__)

DEFAULT_SYSTEM_PROMPT = """You are a helpful AI assistant that provides information about beaches in the USA. 
You can help users find information about beach conditions, weather, tides, and nearby amenities.
Be concise, accurate, and helpful in your responses.
"""

class BeachAgent(BaseAgent):
    """Agent specialized in providing beach information."""
    
    def __init__(
        self,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        tools: Optional[List[Tool]] = None,
        max_memory: int = 20,
        **kwargs
    ):
        """Initialize the beach information agent."""
        super().__init__(
            system_prompt=system_prompt,
            tools=tools or [],
            max_memory=max_memory,
            **kwargs
        )
        self.settings = get_settings()
    
    async def process_message(
        self,
        message: str,
        **kwargs
    ) -> str:
        """Process a user message and return the agent's response."""
        # Add user message to memory
        self.memory.add_message(Message(
            role="user",
            content=message
        ))
        
        try:
            # Get messages in the format expected by LiteLLM
            messages = self._prepare_messages()
            
            # Get response from the language model
            response = await self._get_llm_response(messages)
            
            # Handle tool calls if present
            if hasattr(response, 'tool_calls') and response.tool_calls:
                tool_responses = await self._handle_tool_calls(response.tool_calls)
                # Add tool responses to the conversation
                for tool_response in tool_responses:
                    self.memory.add_message(tool_response)
                
                # Get a new response that incorporates the tool results
                messages = self._prepare_messages()
                response = await self._get_llm_response(messages)
            
            # Extract the text content from the response
            if hasattr(response, 'choices') and response.choices and hasattr(response.choices[0].message, 'content'):
                response_text = response.choices[0].message.content or "I don't have a response for that."
            else:
                response_text = str(response) if response else "I don't have a response for that."
            
            # Add assistant's response to memory
            assistant_message = Message(
                role="assistant",
                content=response_text
            )
            self.memory.add_message(assistant_message)
            
            return response_text
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
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
