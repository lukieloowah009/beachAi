"""
Main FastAPI application for the Beach Information AI Assistant.
"""
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings

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

# Example endpoint
@app.get("/api/v1/beaches/{beach_name}")
async def get_beach_info(beach_name: str):
    """Get information about a specific beach.
    
    Args:
        beach_name: Name of the beach to get information about
        
    Returns:
        dict: Beach information
    """
    # This is a placeholder implementation
    return {
        "name": beach_name,
        "message": "Beach information endpoint is working",
        "data": None,
    }
