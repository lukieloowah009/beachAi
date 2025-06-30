"""Client for interacting with the NOAA Tides & Currents API."""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

import httpx
from pydantic import HttpUrl, ValidationError

from app.config import get_settings
from app.models.noaa_models import (
    NoaaStation,
    NoaaTidePrediction,
    NoaaTidePredictionsResponse,
    NoaaWaterTemperatureData,
    NoaaWaterTemperatureResponse,
)

logger = logging.getLogger(__name__)


class NoaaApiClient:
    """Client for NOAA Tides & Currents API."""
    
    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        """Initialize the NOAA API client.
        
        Args:
            client: Optional httpx.AsyncClient instance (for testing)
        """
        self.settings = get_settings()
        self.base_url = self.settings.NOAA_API_BASE_URL.rstrip("/") + "/"
        self.timeout = self.settings.NOAA_API_TIMEOUT
        self._client = client or httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            follow_redirects=True,
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
    ) -> Dict:
        """Make an HTTP request to the NOAA API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            params: Query parameters
            
        Returns:
            Dict containing the JSON response
            
        Raises:
            httpx.HTTPStatusError: If the request fails
        """
        url = f"{self.base_url}{endpoint.lstrip('/')}"
        logger.debug(
            "Making %s request to %s with params: %s",
            method,
            url,
            params
        )
        
        try:
            response = await self._client.request(
                method=method,
                url=url,
                params=params or {},
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(
                "HTTP error %s: %s",
                e.response.status_code,
                e.response.text,
            )
            raise
        except Exception as e:
            logger.error("Error making request to NOAA API: %s", str(e))
            raise
    
    async def get_tide_predictions(
        self,
        station_id: str,
        begin_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None,
        date: Optional[Union[str, datetime]] = None,
        interval: Optional[str] = None,
        datum: str = "MLLW",
        units: str = "english",
        time_zone: str = "gmt",
    ) -> List[NoaaTidePrediction]:
        """Get tide predictions for a station.
        
        Args:
            station_id: NOAA station ID
            begin_date: Start date (YYYYMMDD or datetime object)
            end_date: End date (YYYYMMDD or datetime object)
            date: Single date (YYYYMMDD or datetime object)
            interval: Prediction interval (h for hourly, hilo for high/low)
            datum: Datum to use for predictions (MLLW, MSL, etc.)
            units: Units for predictions (english or metric)
            time_zone: Time zone for predictions (gmt, lst, lst_ldt)
            
        Returns:
            List of tide predictions
        """
        endpoint = f"stations/{station_id}/tide_predictions.json"
        
        # Format dates
        if date:
            if isinstance(date, datetime):
                date = date.strftime("%Y%m%d")
            begin_date = date
            end_date = date
        else:
            if not begin_date:
                begin_date = datetime.utcnow()
            if not end_date:
                end_date = begin_date + timedelta(days=1)
                
            if isinstance(begin_date, datetime):
                begin_date = begin_date.strftime("%Y%m%d")
            if isinstance(end_date, datetime):
                end_date = end_date.strftime("%Y%m%d")
        
        params = {
            "begin_date": begin_date,
            "end_date": end_date,
            "datum": datum,
            "units": units,
            "time_zone": time_zone,
            "application": "beach-ai",
            "format": "json",
        }
        
        if interval:
            params["interval"] = interval
        
        data = await self._make_request("GET", endpoint, params=params)
        
        try:
            response = NoaaTidePredictionsResponse(**data)
            return response.predictions
        except ValidationError as e:
            logger.error("Error validating tide predictions response: %s", str(e))
            raise
    
    async def get_water_temperature(
        self,
        station_id: str,
        begin_date: Optional[Union[str, datetime]] = None,
        end_date: Optional[Union[str, datetime]] = None,
        date: Optional[Union[str, datetime]] = None,
        units: str = "metric",
        time_zone: str = "gmt",
    ) -> List[NoaaWaterTemperatureData]:
        """Get water temperature data for a station.
        
        Args:
            station_id: NOAA station ID
            begin_date: Start date (YYYYMMDD or datetime object)
            end_date: End date (YYYYMMDD or datetime object)
            date: Single date (YYYYMMDD or datetime object)
            units: Units for temperature (english or metric)
            time_zone: Time zone for data (gmt, lst, lst_ldt)
            
        Returns:
            List of water temperature data points
        """
        endpoint = f"stations/{station_id}/water_temperature.json"
        
        # Format dates
        if date:
            if isinstance(date, datetime):
                date = date.strftime("%Y%m%d")
            begin_date = date
            end_date = date
        else:
            if not begin_date:
                begin_date = datetime.utcnow() - timedelta(days=1)
            if not end_date:
                end_date = datetime.utcnow()
                
            if isinstance(begin_date, datetime):
                begin_date = begin_date.strftime("%Y%m%d")
            if isinstance(end_date, datetime):
                end_date = end_date.strftime("%Y%m%d")
        
        params = {
            "begin_date": begin_date,
            "end_date": end_date,
            "units": units,
            "time_zone": time_zone,
            "application": "beach-ai",
            "format": "json",
        }
        
        data = await self._make_request("GET", endpoint, params=params)
        
        try:
            response = NoaaWaterTemperatureResponse(**data)
            return response.data
        except ValidationError as e:
            logger.error(
                "Error validating water temperature response: %s",
                str(e)
            )
            raise
    
    async def find_stations(
        self,
        lat: float,
        lng: float,
        radius: float = 50.0,
        units: str = "metric",
    ) -> List[NoaaStation]:
        """Find tide stations near a location.
        
        Args:
            lat: Latitude of the search location
            lng: Longitude of the search location
            radius: Search radius in kilometers
            units: Distance units (metric or english)
            
        Returns:
            List of nearby stations
        """
        endpoint = "stations.json"
        
        params = {
            "lat": lat,
            "lng": lng,
            "radius": radius,
            "units": units,
            "application": "beach-ai",
            "format": "json",
        }
        
        data = await self._make_request("GET", endpoint, params=params)
        
        try:
            stations = []
            for station_data in data.get("stations", []):
                try:
                    station = NoaaStation(**station_data)
                    stations.append(station)
                except ValidationError as e:
                    logger.warning("Invalid station data: %s", str(e))
            return stations
        except Exception as e:
            logger.error("Error processing stations response: %s", str(e))
            raise
