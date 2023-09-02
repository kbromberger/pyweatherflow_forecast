"""
This module contains the code to get forecast from
WeatherFlows Better Forecast API.
"""
from __future__ import annotations

import aiohttp

from aiohttp import client_exceptions
from collections import OrderedDict
from typing import Optional

from .const import WEATHERFLOW_FORECAST_URL


class WeatherFlowForecast:
    """Class to hold the Forecast data."""

    def __init__(
            self,
            station_id: int,
            api_token: str,
            session: aiohttp.ClientSession = None
    ) -> None:
        self._station_id = station_id
        self._api_token = api_token

        if session:
            self._session = session
