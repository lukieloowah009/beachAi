"""LLM utilities for the Beach Information AI Assistant."""
import os
from typing import Any, Dict, List, Optional

import litellm
from litellm import completion, acompletion

from app.config import get_settings

# Get settings
settings = get_settings()

# Configure LiteLLM
litellm.set_verbose = settings.DEBUG

# Set Ollama API base
os.environ["OLLAMA_API_BASE"] = settings.OLLAMA_API_BASE


class LLMClient:
    """LLM client for interacting with the language model."""
    
    def __init__(self, model: Optional[str] = None):
        """Initialize the LLM client.
        
        Args:
            model: The model to use. Defaults to the one specified in settings.
        """
        self.model = model or settings.OLLAMA_MODEL
    
    async def generate(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> Any:
        """Generate text from the LLM using a conversation history.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            temperature: Controls randomness (0.0 to 1.0)
            max_tokens: Maximum number of tokens to generate
            tools: Optional list of tool definitions for function calling
            **kwargs: Additional arguments to pass to the LLM
            
        Returns:
            Any: The full response object from the LLM
        """
        try:
            # Prepare the parameters
            params = {
                "model": f"ollama/{self.model}",
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                **kwargs,
            }
            
            # Add tools if provided
            if tools:
                params["tools"] = tools
                
            # Make the API call and return the full response
            return await litellm.acompletion(**params)
            
        except Exception as e:
            logger.error(f"Error generating text: {str(e)}", exc_info=True)
            raise


# Create a default LLM client
llm_client = LLMClient()
