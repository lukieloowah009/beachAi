"""Test cases for the BeachAgent."""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

# Enable asyncio support for pytest
pytestmark = pytest.mark.asyncio

from app.agent import BeachAgent, Tool, Message

# Sample tool for testing
async def mock_weather_tool(location: str) -> dict:
    """Mock weather tool for testing."""
    return {"location": location, "temperature": 75, "conditions": "sunny"}

@pytest.fixture
def beach_agent():
    """Create a test BeachAgent instance."""
    # Create a test tool
    weather_tool = Tool(
        name="get_weather",
        description="Get the current weather for a location",
        parameters={
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "The city and state, e.g., San Francisco, CA"}
            },
            "required": ["location"]
        },
        function=mock_weather_tool
    )
    
    # Create agent with the test tool
    agent = BeachAgent(tools=[weather_tool])
    return agent

@pytest.mark.asyncio
async def test_agent_initialization(beach_agent):
    """Test that the agent initializes correctly."""
    assert beach_agent is not None
    assert len(beach_agent.get_conversation_history()) == 1  # System message

@pytest.mark.asyncio
async def test_agent_response(beach_agent):
    """Test that the agent can respond to a message."""
    response = await beach_agent.process_message("Hello, can you tell me about Santa Monica beach?")
    
    # Basic assertions
    assert response is not None
    assert isinstance(response, str)
    assert len(response) > 0
    
    # Check that the conversation history was updated
    history = beach_agent.get_conversation_history()
    assert len(history) == 3  # System + User + Assistant
    assert history[1]["role"] == "user"
    assert history[2]["role"] == "assistant"

@pytest.mark.asyncio
async def test_agent_with_tools(beach_agent):
    """Test that the agent can use tools."""
    # This test is more complex as it requires the LLM to decide to use the tool
    # For now, we'll just test that the tool is available
    assert "get_weather" in [tool.name for tool in beach_agent.tools.values()]

@pytest.mark.asyncio
async def test_agent_clear_memory(beach_agent):
    """Test that clearing the agent's memory works."""
    # Add some messages
    await beach_agent.process_message("First message")
    await beach_agent.process_message("Second message")
    
    # Clear memory
    beach_agent.clear_memory()
    
    # Check that only the system message remains
    history = beach_agent.get_conversation_history()
    assert len(history) == 1  # Just system message
    assert history[0]["role"] == "system"
