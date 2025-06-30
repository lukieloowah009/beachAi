"""Configuration settings for the Beach Information AI Assistant."""
import os
from functools import lru_cache
from typing import Optional

from pydantic import HttpUrl, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    APP_NAME: str = Field(
        default="Beach Information AI Assistant",
        description="Name of the application",
        env="APP_NAME"
    )
    
    DEBUG: bool = Field(
        default=True,
        description="Enable debug mode",
        env="DEBUG"
    )
    
    ENVIRONMENT: str = Field(
        default="development",
        description="Current environment (development, staging, production)",
        env="ENVIRONMENT"
    )
    
    # Ollama
    OLLAMA_API_BASE: str = Field(
        default="http://localhost:11434",
        description="Base URL for the Ollama API",
        env="OLLAMA_API_BASE"
    )
    
    OLLAMA_MODEL: str = Field(
        default="llama3.2",
        description="Default Ollama model to use",
        env="OLLAMA_MODEL"
    )
    
    # External APIs
    GOOGLE_PLACES_API_KEY: Optional[str] = Field(
        default=None,
        description="API key for Google Places API",
        env="GOOGLE_PLACES_API_KEY"
    )
    
    NOAA_API_BASE_URL: str = Field(
        default="https://api.tidesandcurrents.noaa.gov/api/prod/",
        description="Base URL for NOAA Tides & Currents API",
        env="NOAA_API_BASE_URL"
    )
    
    NOAA_API_TIMEOUT: int = Field(
        default=10,
        description="Timeout in seconds for NOAA API requests",
        env="NOAA_API_TIMEOUT"
    )
    
    NOAA_API_KEY: Optional[str] = Field(
        default=None,
        description="API key for NOAA API",
        env="NOAA_API_KEY"
    )
    
    # CORS
    CORS_ORIGINS: list[str] = Field(
        default=["*"],
        description="List of allowed CORS origins",
        env="CORS_ORIGINS"
    )
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = 'ignore'  # Ignore extra fields in .env file
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get application settings.
    
    Returns:
        Settings: Application settings
    """
    return Settings()
