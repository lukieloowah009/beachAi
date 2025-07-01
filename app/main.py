"""
Main FastAPI application for the Beach Information AI Assistant.
"""
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings

import logging
logging.basicConfig(level=logging.DEBUG)

# Initialize FastAPI app
app = FastAPI(
    title="Beach Information AI Assistant",
    description="An AI-powered assistant for beach information in the USA",
    version="0.1.0",
)

# Get settings
settings = get_settings()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint.
    
    Returns:
        dict: Status of the application
    """
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
    }

from app.agent.beach_agent import BeachAgent
from app.services.google_places_client import GooglePlacesClient
from app.services.noaa_client import NoaaApiClient
from app.services.noaa_nws_client import NoaaNwsClient

# Instantiate API clients ONCE
google_places_client = GooglePlacesClient()
noaa_client = NoaaApiClient()
noaa_nws_client = NoaaNwsClient()
beach_agent = BeachAgent(
    google_places_client=google_places_client,
    noaa_client=noaa_client,
    noaa_nws_client=noaa_nws_client
)

# All endpoints below use this beach_agent instance

import re

def markdown_to_plain_text(md: str) -> str:
    """Convert markdown to plain text for easier reading in Swagger."""
    # Remove bold, italics, and inline code
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", md)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    # Replace bullet points with dashes
    text = re.sub(r"^\s*\* ", "- ", text, flags=re.MULTILINE)
    # Replace newlines with actual line breaks (for Swagger, use <br> or leave as is)
    text = text.replace("\n", "\n")  # Swagger will still show \n, but this is the best we can do in JSON
    return text

from fastapi import Body
from pydantic import BaseModel, Field
from typing import List, Optional

class ChatMessage(BaseModel):
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")

class ChatRequest(BaseModel):
    message: str = Field(..., description="User's message to the agent")

class ChatResponse(BaseModel):
    message: str = Field(..., description="Agent's markdown-formatted reply")

@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat_endpoint(
    chat: ChatRequest = Body(..., example={
        "message": "What are the best beaches for surfing in Florida?"
    })
):
    """General chat endpoint for free-form questions to the BeachAgent."""
    agent_response = await beach_agent.process_message(chat.message)
    return ChatResponse(message=agent_response)

@app.get("/api/v1/beaches/{beach_name}")
async def get_beach_info(beach_name: str):
    """Get information about a specific beach via the BeachAgent.
    
    Args:
        beach_name: Name of the beach to get information about
    Returns:
        dict: Beach information from the agent
    """
    user_message = f"Tell me about {beach_name} beach."
    agent_response = await beach_agent.process_message(user_message)
    return {
        "name": beach_name,
        "message": agent_response,
    }

