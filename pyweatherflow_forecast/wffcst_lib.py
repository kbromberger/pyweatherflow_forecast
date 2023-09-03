"""
This module contains the code to get forecast from
WeatherFlows Better Forecast API.
"""
from __future__ import annotations

import abc
import json

from collections import OrderedDict
from typing import List, Any, Dict
from urllib.request import urlopen

import aiohttp

from .const import WEATHERFLOW_FORECAST_URL


class WeatherFlowForecastException(Exception):
    """Exception thrown if failing to access API"""


class WeatherFlowAPIBase:
    """
    Baseclass to use as dependency injection pattern for easier
    automatic testing
    """

    @abc.abstractmethod
    def get_forecast_api(self, station_id: int, api_token: str) -> Dict[str, Any]:
        """Override this"""
        raise NotImplementedError(
            "users must define get_forecast to use this base class"
        )

    @abc.abstractmethod
    async def async_get_forecast_api(
        self, station_id: int, api_token: str
    ) -> Dict[str, Any]:
        """Override this"""
        raise NotImplementedError(
            "users must define get_forecast to use this base class"
        )


class WeatherFlowAPI(WeatherFlowAPIBase):
    """Default implementation for WeatherFlow Forecast api"""

    def __init__(self) -> None:
        """Init the API with or without session"""
        self.session = None

    def get_forecast_api(self, station_id: int, api_token: str) -> Dict[str, Any]:
        """gets data from API"""
        api_url = f"{WEATHERFLOW_FORECAST_URL}{station_id}&token={api_token}"

        response = urlopen(api_url)
        data = response.read().decode("utf-8")
        json_data = json.loads(data)

        return json_data

    async def async_get_forecast_api(
        self, station_id: int, api_token: str
    ) -> Dict[str, Any]:
        """gets data from API asynchronous"""
        api_url = f"{WEATHERFLOW_FORECAST_URL}{station_id}&token={api_token}"

        is_new_session = False
        if self.session is None:
            self.session = aiohttp.ClientSession()
            is_new_session = True

        async with self.session.get(api_url) as response:
            if response.status != 200:
                if is_new_session:
                    await self.session.close()
                raise WeatherFlowForecastException(
                    f"Failed to access weather API with status code {response.status}"
                )
            data = await response.text()
            if is_new_session:
                await self.session.close()

            return json.loads(data)


class WeatherFlowForecast:
    """Class to hold the Forecast data."""

    def __init__(
        self, station_id: int, api_token: str, session: aiohttp.ClientSession = None
    ) -> None:
        self._station_id = station_id
        self._api_token = api_token

        if session:
            self._session = session
