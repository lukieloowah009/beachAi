"""Data models for Google Places API responses."""
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any, Union, Literal, Annotated
from pydantic import BaseModel, Field, validator, HttpUrl, field_validator, BeforeValidator, ConfigDict


def convert_price_level(value: Any) -> Optional[str]:
    """Convert price level from various input types to string enum."""
    if value is None:
        return None
    if isinstance(value, str):
        return value.lower()
    if isinstance(value, int):
        return {
            0: "free",
            1: "inexpensive",
            2: "moderate",
            3: "expensive",
            4: "very_expensive"
        }.get(value, None)
    return None


class PlacePriceLevel(str, Enum):
    """Price level for a place."""
    FREE = "free"
    INEXPENSIVE = "inexpensive"
    MODERATE = "moderate"
    EXPENSIVE = "expensive"
    VERY_EXPENSIVE = "very_expensive"


class PlaceOpeningHoursPeriodDetail(BaseModel):
    """Details about when a place opens or closes."""
    day: int = Field(..., ge=0, le=6, description="Day of the week (0-6, where 0 is Sunday)")
    time: str = Field(..., pattern=r'^([0-1]?[0-9]|2[0-3])[0-5][0-9]$', description="24-hour time in HHMM format")


class PlaceOpeningHoursPeriod(BaseModel):
    """Period during which the place is open."""
    open: PlaceOpeningHoursPeriodDetail
    close: Optional[PlaceOpeningHoursPeriodDetail] = None


class PlaceOpeningHours(BaseModel):
    """Opening hours for a place."""
    open_now: bool = Field(..., alias="open_now")
    periods: Optional[List[PlaceOpeningHoursPeriod]] = None
    weekday_text: Optional[List[str]] = Field(None, alias="weekday_text")


class PlacePhoto(BaseModel):
    """Photo of a place."""
    height: int
    width: int
    photo_reference: str = Field(..., alias="photo_reference")
    html_attributions: List[str] = Field(default_factory=list, alias="html_attributions")


class PlaceReview(BaseModel):
    """Review for a place."""
    author_name: str = Field(..., alias="author_name")
    author_url: Optional[HttpUrl] = Field(None, alias="author_url")
    language: Optional[str] = None
    original_language: Optional[str] = Field(None, alias="original_language")
    profile_photo_url: Optional[HttpUrl] = Field(None, alias="profile_photo_url")
    rating: float = Field(..., ge=1, le=5)
    relative_time_description: str = Field(..., alias="relative_time_description")
    text: str
    time: datetime
    translated: Optional[bool] = None


class PlaceGeometryLocation(BaseModel):
    """Geographic coordinates of a place."""
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)


class PlaceGeometryViewport(BaseModel):
    """Viewport for displaying a place on a map."""
    northeast: PlaceGeometryLocation
    southwest: PlaceGeometryLocation


class PlaceGeometry(BaseModel):
    """Geometric information about a place."""
    location: PlaceGeometryLocation
    viewport: PlaceGeometryViewport


class Place(BaseModel):
    """Detailed information about a place."""
    model_config = ConfigDict(extra='allow')  # Allow extra fields from API
    
    place_id: str = Field(..., alias="place_id")
    name: str
    formatted_address: str = Field(..., alias="formatted_address")
    geometry: PlaceGeometry
    formatted_phone_number: Optional[str] = Field(None, alias="formatted_phone_number")
    international_phone_number: Optional[str] = Field(None, alias="international_phone_number")
    website: Optional[HttpUrl] = None
    rating: Optional[float] = Field(None, ge=1, le=5)
    user_ratings_total: Optional[int] = Field(None, alias="user_ratings_total", ge=0)
    price_level: Optional[PlacePriceLevel] = Field(
        None, 
        alias="price_level",
        description="Price level from 0 (free) to 4 (very expensive)"
    )
    types: List[str] = Field(default_factory=list)
    opening_hours: Optional[PlaceOpeningHours] = Field(None, alias="opening_hours")
    photos: Optional[List[PlacePhoto]] = None
    reviews: Optional[List[PlaceReview]] = None
    permanently_closed: Optional[bool] = Field(None, alias="permanently_closed")
    business_status: Optional[str] = Field(None, alias="business_status")
    vicinity: Optional[str] = None
    url: Optional[HttpUrl] = None
    utc_offset: Optional[int] = Field(None, alias="utc_offset")
    adr_address: Optional[str] = Field(None, alias="adr_address")
    plus_code: Optional[Dict[str, Any]] = Field(None, alias="plus_code")
    reference: Optional[str] = None
    scope: Optional[str] = None
    
    @validator('types', pre=True)
    def ensure_types_list(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        return v
        
    @validator('price_level', pre=True)
    def validate_price_level(cls, v):
        if v is None:
            return None
        if isinstance(v, int) and 0 <= v <= 4:
            return list(PlacePriceLevel)[v].value
        if isinstance(v, str) and v.lower() in [e.value for e in PlacePriceLevel]:
            return v.lower()
        return None


class PlaceSearchResult(BaseModel):
    """Search result from Google Places API."""
    place_id: str = Field(..., alias="place_id")
    name: str
    formatted_address: str = Field(..., alias="formatted_address")
    geometry: PlaceGeometry
    rating: Optional[float] = Field(None, ge=1, le=5)
    user_ratings_total: Optional[int] = Field(None, alias="user_ratings_total", ge=0)
    price_level: Optional[Union[int, PlacePriceLevel]] = Field(None, alias="price_level")
    types: List[str] = Field(default_factory=list)
    business_status: Optional[str] = Field(None, alias="business_status")
    plus_code: Optional[Dict[str, Any]] = Field(None, alias="plus_code")
    opening_hours: Optional[Dict[str, bool]] = Field(None, alias="opening_hours")
    permanently_closed: Optional[bool] = Field(None, alias="permanently_closed")
    photos: Optional[List[Dict[str, Any]]] = None
    
    @validator('types', pre=True)
    def ensure_types_list(cls, v):
        if v is None:
            return []
        return v


class PlaceSearchResponse(BaseModel):
    """Response from Google Places API search."""
    results: List[PlaceSearchResult]
    next_page_token: Optional[str] = Field(None, alias="next_page_token")
    status: str
    error_message: Optional[str] = Field(None, alias="error_message")
