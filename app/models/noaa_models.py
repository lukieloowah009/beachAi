"""Data models for NOAA Tides & Currents API responses."""
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl


class NoaaTidePrediction(BaseModel):
    """Model for NOAA tide prediction data point."""
    t: str = Field(..., description="Timestamp in ISO 8601 format")
    v: str = Field(..., description="Water level in feet")
    type: Optional[str] = Field(
        None,
        description="Type of tide (e.g., 'H' for high, 'L' for low)"
    )


class NoaaTidePredictionsResponse(BaseModel):
    """Response model for NOAA tide predictions."""
    predictions: List[NoaaTidePrediction] = Field(
        ...,
        description="List of tide predictions"
    )


class NoaaWaterTemperatureData(BaseModel):
    """Model for NOAA water temperature data."""
    t: str = Field(..., description="Timestamp in ISO 8601 format")
    v: str = Field(..., description="Water temperature in Celsius")


class NoaaWaterTemperatureResponse(BaseModel):
    """Response model for NOAA water temperature data."""
    data: List[NoaaWaterTemperatureData] = Field(
        ...,
        description="List of water temperature readings"
    )


class NoaaStation(BaseModel):
    """Model for NOAA station information."""
    id: str = Field(..., description="Station ID")
    name: str = Field(..., description="Station name")
    lat: float = Field(..., description="Latitude")
    lng: float = Field(..., description="Longitude")
    state: Optional[str] = Field(None, description="State code")
    distance: Optional[float] = Field(
        None,
        description="Distance from search location in kilometers"
    )
