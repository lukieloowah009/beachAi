"""Tests for the NOAA API client."""
import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import ANY

import httpx
from app.services.noaa_client import NoaaApiClient
from app.models.noaa_models import (
    NoaaTidePrediction,
    NoaaStation,
    NoaaTidePredictionsResponse,
    NoaaWaterTemperatureData,
    NoaaWaterTemperatureResponse,
)


@pytest.fixture
def mock_tide_predictions_response():
    """Mock response for tide predictions."""
    return {
        "predictions": [
            {"t": "2023-01-01 01:23", "v": "5.2", "type": "H"},
            {"t": "2023-01-01 07:45", "v": "0.8", "type": "L"},
            {"t": "2023-01-01 14:12", "v": "5.8", "type": "H"},
            {"t": "2023-01-01 20:30", "v": "1.2", "type": "L"},
        ]
    }


@pytest.fixture
def mock_water_temp_response():
    """Mock response for water temperature."""
    return {
        "data": [
            {"t": "2023-01-01 00:00", "v": "12.3"},
            {"t": "2023-01-01 01:00", "v": "12.4"},
            {"t": "2023-01-01 02:00", "v": "12.5"},
        ]
    }


@pytest.fixture
def mock_stations_response():
    """Mock response for stations."""
    return {
        "stations": [
            {
                "id": "9414290",
                "name": "San Francisco, CA",
                "lat": 37.8067,
                "lng": -122.4653,
                "state": "CA",
                "distance": 1.5
            },
            {
                "id": "9414750",
                "name": "Alameda, CA",
                "lat": 37.7717,
                "lng": -122.3000,
                "state": "CA",
                "distance": 10.2
            }
        ]
    }


@pytest.mark.asyncio
async def test_get_tide_predictions(noaa_client, mock_httpx_client, mock_tide_predictions_response):
    """Test getting tide predictions from NOAA API."""
    # Setup mock response with request object
    mock_request = httpx.Request("GET", "https://api.tidesandcurrents.noaa.gov/api/prod/")
    mock_httpx_client.request.return_value = httpx.Response(
        200,
        json=mock_tide_predictions_response,
        request=mock_request
    )
    
    # Call the method
    predictions = await noaa_client.get_tide_predictions(
        station_id="9414290",
        date=datetime(2023, 1, 1),
        interval="hilo"
    )
    
    # Verify the request was made correctly
    mock_httpx_client.request.assert_awaited_once()
    
    # Get the actual call arguments
    call_args = mock_httpx_client.request.await_args
    
    # Check the request parameters
    assert call_args.kwargs["method"] == "GET"
    assert "stations/9414290/tide_predictions.json" in call_args.kwargs["url"]
    assert call_args.kwargs["params"] == {
        "begin_date": "20230101",
        "end_date": "20230101",
        "interval": "hilo",
        "datum": "MLLW",
        "units": "english",
        "time_zone": "gmt",
        "application": "beach-ai",
        "format": "json"
    }
    
    # Verify the response
    assert len(predictions) == 4
    assert isinstance(predictions[0], NoaaTidePrediction)
    assert predictions[0].t == "2023-01-01 01:23"
    assert predictions[0].v == "5.2"
    assert predictions[0].type == "H"


@pytest.mark.asyncio
async def test_find_stations(noaa_client, mock_httpx_client, mock_stations_response):
    """Test finding stations near a location."""
    # Setup mock response with request object
    mock_request = httpx.Request("GET", "https://api.tidesandcurrents.noaa.gov/api/prod/")
    mock_httpx_client.request.return_value = httpx.Response(
        200,
        json=mock_stations_response,
        request=mock_request
    )
    
    # Call the method
    stations = await noaa_client.find_stations(
        lat=37.7749,
        lng=-122.4194,
        radius=50
    )
    
    # Verify the request was made correctly
    mock_httpx_client.request.assert_awaited_once()
    
    # Get the actual call arguments
    call_args = mock_httpx_client.request.await_args
    
    # Check the request parameters
    assert call_args.kwargs["method"] == "GET"
    assert call_args.kwargs["url"].endswith("stations.json")
    assert call_args.kwargs["params"] == {
        "lat": 37.7749,
        "lng": -122.4194,
        "radius": 50,
        "units": "metric",
        "application": "beach-ai",
        "format": "json"
    }
    
    # Verify the response
    assert len(stations) == 2
    assert isinstance(stations[0], NoaaStation)
    assert stations[0].id == "9414290"
    assert stations[0].name == "San Francisco, CA"
    assert stations[0].lat == 37.8067
    assert stations[0].lng == -122.4653
    assert stations[0].state == "CA"
    assert stations[0].distance == 1.5
    
    # Verify stations are sorted by distance
    assert stations[0].distance == 1.5
    assert stations[1].distance == 10.2


@pytest.mark.asyncio
async def test_get_water_temperature(noaa_client, mock_httpx_client, mock_water_temp_response):
    """Test getting water temperature data."""
    # Setup mock response with request object
    mock_request = httpx.Request("GET", "https://api.tidesandcurrents.noaa.gov/api/prod/")
    mock_httpx_client.request.return_value = httpx.Response(
        200,
        json=mock_water_temp_response,
        request=mock_request
    )
    
    # Call the method
    temps = await noaa_client.get_water_temperature(
        station_id="9414290",
        begin_date=datetime(2023, 1, 1),
        end_date=datetime(2023, 1, 2),
        units="metric"
    )
    
    # Verify the request was made correctly
    mock_httpx_client.request.assert_awaited_once()
    
    # Get the actual call arguments
    call_args = mock_httpx_client.request.await_args
    
    # Check the request parameters
    assert call_args.kwargs["method"] == "GET"
    assert "stations/9414290/water_temperature.json" in call_args.kwargs["url"]
    assert call_args.kwargs["params"] == {
        "begin_date": "20230101",
        "end_date": "20230102",
        "units": "metric",
        "time_zone": "gmt",
        "application": "beach-ai",
        "format": "json"
    }
    
    # Verify the response
    assert len(temps) == 3
    assert isinstance(temps[0], NoaaWaterTemperatureData)
    assert temps[0].t == "2023-01-01 00:00"
    assert temps[0].v == "12.3"
