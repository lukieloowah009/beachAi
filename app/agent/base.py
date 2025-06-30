"""Base agent implementation with conversation memory and tool integration."""
from typing import Dict, List, Optional, Any, Callable, TypeVar, Generic
from pydantic import BaseModel, Field
import json

T = TypeVar('T', bound=BaseModel)

class Tool(BaseModel):
    """A tool that can be called by the agent."""
    name: str
    description: str
    parameters: dict
    function: Callable[..., Any]

    def to_dict(self) -> dict:
        """Convert tool to a dictionary for the LLM."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }


class Message(BaseModel):
    """A message in the conversation."""
    role: str  # 'user', 'assistant', 'system', or 'tool'
    content: str
    name: Optional[str] = None
    tool_call_id: Optional[str] = None


class ConversationMemory:
    """Manages conversation history and context."""
    
    def __init__(self, max_messages: int = 20):
        """Initialize with a maximum number of messages to retain."""
        self.messages: List[Message] = []
        self.max_messages = max_messages
    
    def add_message(self, message: Message) -> None:
        """Add a message to the conversation history."""
        self.messages.append(message)
        # Trim old messages if we're over the limit
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
    
    def get_messages(self) -> List[Dict[str, Any]]:
        """Get all messages in a format suitable for the LLM."""
        return [msg.model_dump(exclude_none=True) for msg in self.messages]
    
    def clear(self) -> None:
        """Clear the conversation history."""
        self.messages = []


class BaseAgent(Generic[T]):
    """Base class for AI agents with conversation memory and tool support."""
    
    def __init__(
        self,
        system_prompt: str,
        tools: Optional[List[Tool]] = None,
        max_memory: int = 20,
        **kwargs
    ):
        """Initialize the agent.
        
        Args:
            system_prompt: The system prompt to guide the agent's behavior
            tools: List of tools the agent can use
            max_memory: Maximum number of messages to retain in memory
        """
        self.system_prompt = system_prompt
        self.memory = ConversationMemory(max_messages=max_memory)
        self.tools = {tool.name: tool for tool in (tools or [])}
        self._initialize_conversation()
    
    def _initialize_conversation(self) -> None:
        """Initialize the conversation with the system prompt."""
        self.memory.clear()
        self.memory.add_message(Message(
            role="system",
            content=self.system_prompt
        ))
    
    def add_tool(self, tool: Tool) -> None:
        """Add a tool to the agent's toolkit."""
        self.tools[tool.name] = tool
    
    async def process_message(
        self,
        message: str,
        **kwargs
    ) -> str:
        """Process a user message and return the agent's response.
        
        This is the main entry point for interacting with the agent.
        Subclasses should implement this method.
        """
        raise NotImplementedError("Subclasses must implement process_message")
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get the current conversation history."""
        return self.memory.get_messages()
    
    def clear_memory(self) -> None:
        """Clear the agent's conversation memory."""
        self.memory.clear()
        self._initialize_conversation()
