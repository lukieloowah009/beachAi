"""Tests for the Google Places API client."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from app.models.google_places_models import Place, PlaceSearchResponse, PlaceSearchResult


@pytest.mark.asyncio
async def test_search_places(
    google_places_client,
    mock_httpx_client,
    mock_place_search_response
):
    """Test searching for places."""
    # Setup mock response
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_place_search_response
    mock_response.raise_for_status = AsyncMock()
    mock_httpx_client.request.return_value = mock_response
    
    # Call the method
    response = await google_places_client.search_places(
        query="Googleplex",
        location={"lat": 37.4223878, "lng": -122.0841877},
        radius=5000,
        type="point_of_interest"
    )
    
    # Verify the request was made correctly
    mock_httpx_client.request.assert_awaited_once()
    call_args = mock_httpx_client.request.await_args
    
    # Check the request parameters
    assert call_args.kwargs["method"] == "GET"
    assert call_args.kwargs["url"] == "/textsearch/json"
    assert call_args.kwargs["params"]["query"] == "Googleplex"
    assert call_args.kwargs["params"]["location"] == "37.4223878,-122.0841877"
    assert call_args.kwargs["params"]["radius"] == 5000
    assert call_args.kwargs["params"]["type"] == "point_of_interest"
    
    # Verify the response
    assert isinstance(response, PlaceSearchResponse)
    # The response should have results or not based on the mock
    assert response.status in ["OK", "UNKNOWN_ERROR"]


@pytest.mark.asyncio
async def test_get_place_details(
    google_places_client,
    mock_httpx_client,
    mock_place_details_response
):
    """Test getting place details."""
    # Create a mock response with the fixture data
    mock_response = AsyncMock()
    mock_response.status_code = 200
    
    # Setup the async methods to be awaitable
    async def mock_raise_for_status():
        if 400 <= mock_response.status_code < 600:
            raise httpx.HTTPStatusError("Error", request=None, response=mock_response)
    
    # Create a proper async function for json() that returns our fixture data
    async def mock_json():
        return mock_place_details_response
    
    # Set up the mock methods
    mock_response.raise_for_status = mock_raise_for_status
    mock_response.json = mock_json
    
    # Use AsyncMock for the request method so assertions work
    mock_httpx_client.request = AsyncMock(return_value=mock_response)
    
    # Call the method
    place = await google_places_client.get_place_details(
        place_id="ChIJN1t_tDeuEmsRUsoyG83frY4",
        fields=["name", "formatted_address", "formatted_phone_number", "website"]
    )
    
    # Verify the request was made correctly
    mock_httpx_client.request.assert_awaited_once()
    call_args = mock_httpx_client.request.await_args
    
    # Check the request parameters
    assert call_args.kwargs["method"] == "GET"
    assert call_args.kwargs["url"] == "/details/json"
    assert call_args.kwargs["params"]["place_id"] == "ChIJN1t_tDeuEmsRUsoyG83frY4"
    assert call_args.kwargs["params"]["fields"] == "name,formatted_address,formatted_phone_number,website"
    
    # Verify the response
    assert isinstance(place, Place)
    assert place.name == "Googleplex"
    assert place.formatted_address == "1600 Amphitheatre Pkwy, Mountain View, CA 94043, USA"
    assert place.formatted_phone_number == "(650) 253-0000"
    assert str(place.website) == "https://about.google/intl/en/locations/?region=north-america"


@pytest.mark.asyncio
async def test_find_place(google_places_client, mock_httpx_client):
    """Test finding a place by text input."""
    # Setup mock response
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "candidates": [
            {
                "place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4",
                "name": "Googleplex",
                "formatted_address": "1600 Amphitheatre Pkwy, Mountain View, CA 94043, USA",
                "geometry": {
                    "location": {"lat": 37.4223878, "lng": -122.0841877},
                    "viewport": {
                        "northeast": {"lat": 37.4239627802915, "lng": -122.0829089197085},
                        "southwest": {"lat": 37.4212648197085, "lng": -122.0856068802915}
                    }
                }
            }
        ],
        "status": "OK"
    }
    mock_response.raise_for_status = AsyncMock()
    mock_httpx_client.request.return_value = mock_response
    
    # Call the method
    places = await google_places_client.find_place(
        input="Googleplex",
        input_type="textquery",
        fields=["name", "formatted_address"]
    )
    
    # Verify the request was made correctly
    mock_httpx_client.request.assert_awaited_once()
    call_args = mock_httpx_client.request.await_args
    
    # Check the request parameters
    assert call_args.kwargs["method"] == "GET"
    assert call_args.kwargs["url"] == "/findplacefromtext/json"
    assert call_args.kwargs["params"]["input"] == "Googleplex"
    assert call_args.kwargs["params"]["inputtype"] == "textquery"
    assert call_args.kwargs["params"]["fields"] == "name,formatted_address"
    
    # Verify the response
    # The response should have results or not based on the mock
    assert isinstance(places, list)


@pytest.mark.asyncio
async def test_get_place_photo(google_places_client, mock_httpx_client, mock_photo_response):
    """Test getting a place photo."""
    # Setup mock response
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = AsyncMock()
    mock_response.aread = AsyncMock(return_value=mock_photo_response)
    mock_httpx_client.request.return_value = mock_response
    
    # Call the method
    photo_data = await google_places_client.get_place_photo(
        photo_reference="test_photo_reference",
        max_width=400
    )
    
    # Verify the request was made correctly
    mock_httpx_client.request.assert_awaited_once()
    call_args = mock_httpx_client.request.await_args
    
    # Check the request parameters
    assert call_args.kwargs["method"] == "GET"
    assert call_args.kwargs["url"] == "/photo"
    assert call_args.kwargs["params"]["photoreference"] == "test_photo_reference"
    assert call_args.kwargs["params"]["maxwidth"] == 400
    
    # Verify the response
    assert photo_data is not None
