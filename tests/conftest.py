"""Pytest configuration and fixtures."""
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.noaa_client import NoaaApiClient
from app.services.google_places_client import GooglePlacesClient


@pytest.fixture
def mock_httpx_client():
    """Create a mock HTTPX client for testing."""
    return AsyncMock()


@pytest.fixture
def noaa_client(mock_httpx_client):
    """Create a NOAA API client with a mock HTTPX client."""
    return NoaaApiClient(client=mock_httpx_client)


@pytest.fixture
def google_places_client(mock_httpx_client):
    """Create a Google Places API client with a mock HTTPX client."""
    return GooglePlacesClient(client=mock_httpx_client)


@pytest.fixture
def mock_place_search_response():
    """Mock response for place search."""
    return {
        "results": [
            {
                "place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4",
                "name": "Googleplex",
                "formatted_address": "1600 Amphitheatre Pkwy, Mountain View, CA 94043, USA",
                "geometry": {
                    "location": {
                        "lat": 37.4223878,
                        "lng": -122.0841877
                    },
                    "viewport": {
                        "northeast": {
                            "lat": 37.4239627802915,
                            "lng": -122.0829089197085
                        },
                        "southwest": {
                            "lat": 37.4212648197085,
                            "lng": -122.0856068802915
                        }
                    }
                },
                "business_status": "OPERATIONAL",
                "rating": 4.6,
                "user_ratings_total": 1000,
                "types": ["point_of_interest", "establishment"],
                "plus_code": {
                    "compound_code": "CWC8+W9 Mountain View, CA, USA",
                    "global_code": "849VCWC8+W9"
                },
                "photos": [
                    {
                        "height": 3024,
                        "width": 4032,
                        "photo_reference": "test_photo_reference",
                        "html_attributions": []
                    }
                ]
            }
        ],
        "status": "OK"
    }


@pytest.fixture
def mock_place_details_response():
    """Mock response for place details."""
    return {
        "result": {
            "place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4",
            "name": "Googleplex",
            "formatted_address": "1600 Amphitheatre Pkwy, Mountain View, CA 94043, USA",
            "formatted_phone_number": "(650) 253-0000",
            "international_phone_number": "+1 650-253-0000",
            "website": "https://about.google/intl/en/locations/?region=north-america",
            "rating": 4.6,
            "user_ratings_total": 1000,
            "price_level": 3,
            "types": ["point_of_interest", "establishment"],
            "opening_hours": {
                "open_now": True,
                "periods": [
                    {
                        "open": {
                            "day": 0,
                            "time": "0900"
                        },
                        "close": {
                            "day": 0,
                            "time": "1800"
                        }
                    }
                ],
                "weekday_text": [
                    "Monday: 9:00 AM – 6:00 PM",
                    "Tuesday: 9:00 AM – 6:00 PM",
                    "Wednesday: 9:00 AM – 6:00 PM",
                    "Thursday: 9:00 AM – 6:00 PM",
                    "Friday: 9:00 AM – 6:00 PM",
                    "Saturday: Closed",
                    "Sunday: Closed"
                ]
            },
            "photos": [
                {
                    "height": 3024,
                    "width": 4032,
                    "photo_reference": "test_photo_reference",
                    "html_attributions": []
                }
            ],
            "geometry": {
                "location": {
                    "lat": 37.4223878,
                    "lng": -122.0841877
                },
                "viewport": {
                    "northeast": {
                        "lat": 37.4239627802915,
                        "lng": -122.0829089197085
                    },
                    "southwest": {
                        "lat": 37.4212648197085,
                        "lng": -122.0856068802915
                    }
                }
            },
            "business_status": "OPERATIONAL",
            "vicinity": "1600 Amphitheatre Parkway, Mountain View",
            "url": "https://maps.google.com/?cid=10289066590918843342",
            "utc_offset": -420,
            "adr_address": "<span class=\"street-address\">1600 Amphitheatre Pkwy</span>, <span class=\"locality\">Mountain View</span>, <span class=\"region\">CA</span> <span class=\"postal-code\">94043</span>, <span class=\"country-name\">USA</span>",
            "plus_code": {
                "compound_code": "CWC8+W9 Mountain View, CA, USA",
                "global_code": "849VCWC8+W9"
            },
            "reference": "ChIJN1t_tDeuEmsRUsoyG83frY4",
            "scope": "GOOGLE"
        },
        "status": "OK"
    }


@pytest.fixture
def mock_photo_response():
    """Mock binary response for a photo."""
    return b"binary_photo_data"
