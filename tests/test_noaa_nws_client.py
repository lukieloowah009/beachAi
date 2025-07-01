"""Unit tests for the NOAA National Weather Service (NWS) client."""
import pytest
from unittest.mock import AsyncMock, patch
from app.services.noaa_nws_client import NoaaNwsClient

@pytest.mark.asyncio
async def test_get_forecast_success():
    client = NoaaNwsClient()
    lat, lon = 26.2379, -80.1248
    # Patch httpx.AsyncClient.get to mock NWS API responses
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        # Mock /points/{lat,lon} response
        from unittest.mock import MagicMock
        mock_resp1 = MagicMock(status_code=200)
        mock_resp1.json.return_value = {"properties": {"forecast": "https://api.weather.gov/gridpoints/MFL/110,71/forecast"}}
        mock_resp1.raise_for_status = MagicMock()
        mock_resp2 = MagicMock(status_code=200)
        mock_resp2.json.return_value = {"properties": {"periods": [{"name": "Today", "detailedForecast": "Sunny, high near 80."}]}}
        mock_resp2.raise_for_status = MagicMock()
        mock_get.side_effect = [mock_resp1, mock_resp2]
        result = await client.get_forecast(lat, lon)
        assert result is not None
        assert "properties" in result
        assert "periods" in result["properties"]
        assert result["properties"]["periods"][0]["name"] == "Today"

@pytest.mark.asyncio
async def test_get_current_conditions_success():
    client = NoaaNwsClient()
    lat, lon = 26.2379, -80.1248
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        from unittest.mock import MagicMock
        mock_resp1 = MagicMock(status_code=200)
        mock_resp1.json.return_value = {"properties": {"observationStations": "https://api.weather.gov/gridpoints/MFL/110,71/stations"}}
        mock_resp1.raise_for_status = MagicMock()
        mock_resp2 = MagicMock(status_code=200)
        mock_resp2.json.return_value = {"features": [{"properties": {"stationIdentifier": "KPMP"}}]}
        mock_resp2.raise_for_status = MagicMock()
        mock_resp3 = MagicMock(status_code=200)
        mock_resp3.json.return_value = {"properties": {"temperature": {"value": 25.0, "unitCode": "unit:degC"}, "textDescription": "Clear"}}
        mock_resp3.raise_for_status = MagicMock()
        mock_get.side_effect = [mock_resp1, mock_resp2, mock_resp3]
        result = await client.get_current_conditions(lat, lon)
        assert result is not None
        assert "properties" in result
        assert result["properties"]["textDescription"] == "Clear"
        assert result["properties"]["temperature"]["value"] == 25.0

@pytest.mark.asyncio
async def test_get_forecast_error():
    client = NoaaNwsClient()
    lat, lon = 0.0, 0.0
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = Exception("Network error")
        result = await client.get_forecast(lat, lon)
        assert result is None

@pytest.mark.asyncio
async def test_get_current_conditions_error():
    client = NoaaNwsClient()
    lat, lon = 0.0, 0.0
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = Exception("Network error")
        result = await client.get_current_conditions(lat, lon)
        assert result is None
