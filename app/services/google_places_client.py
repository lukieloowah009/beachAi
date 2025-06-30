"""Client for interacting with the Google Places API."""
import logging
from typing import Any, Dict, List, Optional, Union

import httpx
from pydantic import HttpUrl, ValidationError

from app.config import get_settings
from app.models.google_places_models import (
    Place,
    PlaceSearchResponse,
    PlaceSearchResult,
)

logger = logging.getLogger(__name__)


class GooglePlacesClient:
    """Client for Google Places API."""
    
    BASE_URL = "https://maps.googleapis.com/maps/api/place"
    
    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        """Initialize the Google Places API client.
        
        Args:
            client: Optional httpx.AsyncClient instance (for testing)
        """
        self.settings = get_settings()
        self.api_key = self.settings.GOOGLE_PLACES_API_KEY
        self._client = client or httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=10.0,
            follow_redirects=True,
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def close(self) -> None:
        """Close the HTTP client session."""
        await self._client.aclose()
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        is_binary: bool = False
    ) -> Union[Dict[str, Any], bytes]:
        """Make an HTTP request to the Google Places API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., '/nearbysearch/json')
            params: Query parameters
            is_binary: Whether to return binary data (for photos)
            
        Returns:
            Dict containing the JSON response or bytes for binary data
            
        Raises:
            httpx.HTTPStatusError: If the request fails
            ValidationError: If the response cannot be validated
        """
        if params is None:
            params = {}
            
        # Add API key to all requests
        params["key"] = self.api_key
        
        try:
            response = await self._client.request(
                method=method,
                url=endpoint,
                params=params
            )
            
            # For binary responses (like photos), just return the content
            if is_binary:
                response.raise_for_status()
                return await response.aread()
                
            # For JSON responses, parse and return
            logger.debug("Response status: %s", response.status_code)
            logger.debug("Response headers: %s", response.headers)
            
            # Ensure we await the raise_for_status coroutine
            if hasattr(response, 'raise_for_status'):
                await response.raise_for_status()
            
            # Get the response data
            if hasattr(response, 'json') and callable(response.json):
                result = response.json()
                # If result is a coroutine, await it
                if hasattr(result, '__await__'):
                    data = await result
                else:
                    data = result
                logger.debug("Response data (parsed): %s", data)
                return data
            else:
                # If no json method, try to get text and parse manually
                response_text = await response.text()
                logger.debug("Raw response text: %s", response_text)
                try:
                    import json
                    return json.loads(response_text)
                except json.JSONDecodeError as e:
                    logger.error("Failed to parse JSON response: %s", e)
                    logger.error("Response content: %s", response_text)
                    raise ValueError(f"Failed to parse JSON response: {e}") from e
            
        except httpx.HTTPStatusError as e:
            logger.error(
                "HTTP error %s: %s",
                e.response.status_code,
                e.response.text if hasattr(e, 'response') else str(e),
                exc_info=True
            )
            raise
        except Exception as e:
            logger.error("Error making request to Google Places API: %s", str(e), exc_info=True)
            raise
    
    async def search_places(
        self,
        query: Optional[str] = None,
        location: Optional[Dict[str, float]] = None,
        radius: Optional[int] = None,
        type: Optional[str] = None,
        language: str = "en",
        region: Optional[str] = None,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        open_now: bool = False,
        page_token: Optional[str] = None,
    ) -> PlaceSearchResponse:
        """Search for places using Google Places API.
        
        Args:
            query: The text string on which to search, for example: "restaurant"
            location: Dict with 'lat' and 'lng' keys for the center point of the search
            radius: Defines the distance (in meters) within which to return place results
            type: Restricts the results to places matching the specified type
            language: The language code, indicating in which language the results should be returned
            region: The region code, specified as a ccTLD two-character value
            min_price: 0-4, representing increasing price levels
            max_price: 0-4, representing increasing price levels
            open_now: Return only those places that are open for business at the time
            page_token: Token from a previous search that was more than 20 results
            
        Returns:
            PlaceSearchResponse containing search results
        """
        endpoint = "/nearbysearch/json" if query is None else "/textsearch/json"
        params: Dict[str, Any] = {
            "language": language,
        }
        
        if query:
            params["query"] = query
        
        if location:
            params["location"] = f"{location['lat']},{location['lng']}"
        
        if radius is not None:
            params["radius"] = radius
            
        if type:
            params["type"] = type
            
        if region:
            params["region"] = region
            
        if min_price is not None:
            params["minprice"] = min_price
            
        if max_price is not None:
            params["maxprice"] = max_price
            
        if open_now:
            params["opennow"] = "true"
            
        if page_token:
            params["pagetoken"] = page_token
        
        data = await self._make_request("GET", endpoint, params)
        if isinstance(data, dict):
            return PlaceSearchResponse(**data)
        return PlaceSearchResponse(status="UNKNOWN_ERROR", results=[])
    
    async def get_place_details(
        self,
        place_id: str,
        fields: Optional[List[str]] = None,
        language: str = "en",
        region: Optional[str] = None,
        session_token: Optional[str] = None,
    ) -> Place:
        """Get detailed information about a specific place.
        
        Args:
            place_id: A textual identifier that uniquely identifies a place
            fields: List of fields to include in the response
            language: The language code, indicating in which language the results should be returned
            region: The region code, specified as a ccTLD two-character value
            session_token: A token that marks the state of the Place ID
            
        Returns:
            Place object with detailed information
        """
        endpoint = "/details/json"
        params: Dict[str, Any] = {
            "place_id": place_id,
            "language": language,
        }
        
        if fields:
            params["fields"] = ",".join(fields)
            
        if region:
            params["region"] = region
            
        if session_token:
            params["sessiontoken"] = session_token
        
        data = await self._make_request("GET", endpoint, params)
        logger.debug("Response data in get_place_details: %s", data)
        if isinstance(data, dict):
            logger.debug("Response keys: %s", data.keys())
            if "result" in data:
                logger.debug("Result data: %s", data["result"])
                try:
                    place = Place(**data["result"])
                    logger.debug("Successfully created Place object")
                    return place
                except Exception as e:
                    logger.error("Failed to create Place object: %s", e, exc_info=True)
                    raise
        logger.error("Invalid response format: %s", data)
        raise ValueError("Invalid response format from Google Places API")
    
    async def find_place(
        self,
        input: str,
        input_type: str = "textquery",
        fields: Optional[List[str]] = None,
        language: str = "en",
        location_bias: Optional[str] = None,
    ) -> List[PlaceSearchResult]:
        """Find a place using the Google Places API text search.
        
        Args:
            input: The text input specifying which place to search for
            input_type: The type of input (textquery or phonenumber)
            fields: List of fields to include in the response
            language: The language code for the results
            location_bias: Prefer results in a specified area
            
        Returns:
            List of matching places
        """
        endpoint = "/findplacefromtext/json"
        params: Dict[str, Any] = {
            "input": input,
            "inputtype": input_type,
            "language": language,
        }
        
        if fields:
            params["fields"] = ",".join(fields)
            
        if location_bias:
            params["locationbias"] = location_bias
        
        data = await self._make_request("GET", endpoint, params)
        if isinstance(data, dict) and "candidates" in data:
            return [PlaceSearchResult(**candidate) for candidate in data["candidates"]]
        return []
    
    async def get_place_photo(
        self,
        photo_reference: str,
        max_width: Optional[int] = None,
        max_height: Optional[int] = None,
    ) -> bytes:
        """Get a photo from a place using a photo reference.
        
        Args:
            photo_reference: String used to identify the photo to retrieve
            max_width: The maximum desired width of the image
            max_height: The maximum desired height of the image
            
        Returns:
            Bytes containing the photo data
            
        Raises:
            httpx.HTTPStatusError: If the photo request fails
            ValueError: If the photo data is empty
        """
        if not (max_width or max_height):
            max_width = 400  # Default width if none specified
            
        endpoint = "/photo"
        params: Dict[str, Any] = {
            "photoreference": photo_reference,
        }
        
        if max_width:
            params["maxwidth"] = max_width
        if max_height:
            params["maxheight"] = max_height
            
        try:
            photo_data = await self._make_request(
                "GET",
                endpoint,
                params=params,
                is_binary=True
            )
            
            if not photo_data:
                raise ValueError("Received empty photo data from Google Places API")
                
            return photo_data
            
        except Exception as e:
            logger.error("Error fetching photo: %s", str(e), exc_info=True)
            raise
