import httpx
from typing import Optional, Dict, Any

class NoaaNwsClient:
    """
    Client for NOAA National Weather Service (NWS) API.
    Docs: https://www.weather.gov/documentation/services-web-api
    """
    BASE_URL = "https://api.weather.gov"

    def __init__(self, user_agent: str = "beach-ai/1.0 (contact@example.com)"):
        self.user_agent = user_agent
        self.headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/geo+json,application/json"
        }

    async def get_forecast(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """
        Get forecast for a given latitude and longitude.
        Returns a dictionary with forecast data, or None on error.
        """
        async with httpx.AsyncClient() as client:
            # Step 1: Get the forecast office and grid info
            points_url = f"{self.BASE_URL}/points/{lat},{lon}"
            try:
                resp = await client.get(points_url, headers=self.headers, timeout=10)
                resp.raise_for_status()
                points_data = resp.json()
                forecast_url = points_data["properties"]["forecast"]
            except Exception as e:
                print(f"[NWS] Error fetching points data: {e}")
                return None
            # Step 2: Get the forecast
            try:
                resp = await client.get(forecast_url, headers=self.headers, timeout=10)
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                print(f"[NWS] Error fetching forecast: {e}")
                return None

    async def get_current_conditions(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """
        Get current weather conditions for a given latitude and longitude.
        Returns a dictionary with observation data, or None on error.
        """
        async with httpx.AsyncClient() as client:
            # Step 1: Get the nearest observation station
            points_url = f"{self.BASE_URL}/points/{lat},{lon}"
            try:
                resp = await client.get(points_url, headers=self.headers, timeout=10)
                resp.raise_for_status()
                points_data = resp.json()
                stations_url = points_data["properties"]["observationStations"]
            except Exception as e:
                print(f"[NWS] Error fetching observation stations: {e}")
                return None
            # Step 2: Get the latest observation from the first station
            try:
                resp = await client.get(stations_url, headers=self.headers, timeout=10)
                resp.raise_for_status()
                stations_data = resp.json()
                if not stations_data["features"]:
                    return None
                station_id = stations_data["features"][0]["properties"]["stationIdentifier"]
                obs_url = f"{self.BASE_URL}/stations/{station_id}/observations/latest"
                resp = await client.get(obs_url, headers=self.headers, timeout=10)
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                print(f"[NWS] Error fetching current conditions: {e}")
                return None
