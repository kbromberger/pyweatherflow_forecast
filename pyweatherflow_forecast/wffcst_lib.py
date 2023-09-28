"""This module contains the code to get forecast from WeatherFlows Better Forecast API."""

from __future__ import annotations

import abc
import datetime
import json
import logging

from typing import Any
from urllib.request import urlopen

import aiohttp

from .const import (
    ICON_LIST,
    WEATHERFLOW_FORECAST_URL,
    WEATHERFLOW_STATION_URL,
)
from .data import (
    WeatherFlowForecastData,
    WeatherFlowForecastDaily,
    WeatherFlowForecastHourly,
    WeatherFlowStationData,
)

_LOGGER = logging.getLogger(__name__)

class WeatherFlowForecastBadRequest(Exception):
    """Request is invalid."""


class WeatherFlowForecastUnauthorized(Exception):
    """Unauthorized API Key."""


class WeatherFlowForecastWongStationId(Exception):
    """Station ID does not exist."""


class WeatherFlowForecastInternalServerError(Exception):
    """Servers encounter an unexpected error."""


class WeatherFlowAPIBase:
    """Baseclass to use as dependency injection pattern for easier automatic testing."""

    @abc.abstractmethod
    def get_forecast_api(self, station_id: int, api_token: str) -> dict[str, Any]:
        """Override this."""
        raise NotImplementedError(
            "users must define get_forecast to use this base class"
        )

    @abc.abstractmethod
    def get_station_api(self, station_id: int, api_token: str) -> dict[str, Any]:
        """Override this."""
        raise NotImplementedError(
            "users must define get_station to use this base class"
        )

    @abc.abstractmethod
    async def async_get_forecast_api(
        self, station_id: int, api_token: str
    ) -> dict[str, Any]:
        """Override this."""
        raise NotImplementedError(
            "users must define get_forecast to use this base class"
        )

    @abc.abstractmethod
    async def async_get_station_api(
        self, station_id: int, api_token: str
    ) -> dict[str, Any]:
        """Override this."""
        raise NotImplementedError(
            "users must define get_station to use this base class"
        )


class WeatherFlowAPI(WeatherFlowAPIBase):
    """Default implementation for WeatherFlow api."""

    def __init__(self) -> None:
        """Init the API with or without session."""
        self.session = None

    def get_forecast_api(self, station_id: int, api_token: str) -> dict[str, Any]:
        """Return data from API."""
        api_url = f"{WEATHERFLOW_FORECAST_URL}{station_id}&token={api_token}"

        response = urlopen(api_url)
        data = response.read().decode("utf-8")
        json_data = json.loads(data)

        return json_data

    def get_station_api(self, station_id: int, api_token: str) -> dict[str, Any]:
        """Return data from API."""
        api_url = f"{WEATHERFLOW_STATION_URL}{station_id}?token={api_token}"
        _LOGGER.debug("URL: %s", api_url)

        response = urlopen(api_url)
        data = response.read().decode("utf-8")
        json_data = json.loads(data)

        return json_data


    async def async_get_forecast_api(
        self, station_id: int, api_token: str
    ) -> dict[str, Any]:
        """Return data from API asynchronous."""
        api_url = f"{WEATHERFLOW_FORECAST_URL}{station_id}&token={api_token}"

        is_new_session = False
        if self.session is None:
            self.session = aiohttp.ClientSession()
            is_new_session = True

        async with self.session.get(api_url) as response:
            if response.status != 200:
                if is_new_session:
                    await self.session.close()
                if response.status == 400:
                    raise WeatherFlowForecastBadRequest(
                        "400 BAD_REQUEST Requests is invalid in some way (invalid dates, bad location parameter etc)."
                    )
                if response.status == 401:
                    raise WeatherFlowForecastUnauthorized(
                        "401 UNAUTHORIZED The API key is incorrect or your account status is inactive or disabled."
                    )
                if response.status == 500:
                    raise WeatherFlowForecastInternalServerError(
                        "500 INTERNAL_SERVER_ERROR WeatherFlow servers encounter an unexpected error."
                    )

            data = await response.text()
            if is_new_session:
                await self.session.close()

            json_data = json.loads(data)
            fetch_status = json_data["status"]["status_code"]
            _LOGGER.debug("FETCH STATUS DATA: %s", fetch_status)
            if fetch_status == 3:
                raise WeatherFlowForecastWongStationId(
                    f"The Station with ID: {station_id} cannot be found."
                )
            if fetch_status == 401:
                    raise WeatherFlowForecastUnauthorized(
                        "401 UNAUTHORIZED The API token is incorrect or your account status is inactive or disabled."
                    )

            return json_data

    async def async_get_station_api(
        self, station_id: int, api_token: str
    ) -> dict[str, Any]:
        """Return data from API asynchronous."""
        api_url = f"{WEATHERFLOW_STATION_URL}{station_id}?token={api_token}"

        is_new_session = False
        if self.session is None:
            self.session = aiohttp.ClientSession()
            is_new_session = True

        async with self.session.get(api_url) as response:
            if response.status != 200:
                if is_new_session:
                    await self.session.close()
                if response.status == 400:
                    raise WeatherFlowForecastBadRequest(
                        "400 BAD_REQUEST Requests is invalid in some way (invalid dates, bad location parameter etc)."
                    )
                if response.status == 401:
                    raise WeatherFlowForecastUnauthorized(
                        "401 UNAUTHORIZED The API token is incorrect or your account status is inactive or disabled."
                    )
                if response.status == 500:
                    raise WeatherFlowForecastInternalServerError(
                        "500 INTERNAL_SERVER_ERROR WeatherFlow servers encounter an unexpected error."
                    )
            data = await response.text()
            if is_new_session:
                await self.session.close()

            json_data = json.loads(data)
            fetch_status = json_data["status"]["status_code"]
            if fetch_status == 3:
                raise WeatherFlowForecastWongStationId(
                    f"The Station with ID: {station_id} cannot be found."
                )
            if fetch_status == 0:
                _LOGGER.debug("WRONG API: %s", json_data["stations"]["capabilities"])
                if json_data["stations"]["capabilities"] is None:
                    raise WeatherFlowForecastUnauthorized(
                        "401 UNAUTHORIZED The API token is incorrect or your account status is inactive or disabled."
                    )
            if fetch_status == 401:
                    raise WeatherFlowForecastUnauthorized(
                        "401 UNAUTHORIZED The API token is incorrect or your account status is inactive or disabled."
                    )
            return json_data


class WeatherFlow:
    """Class that uses the Better Forecast API from WeatherFlow to retreive forecast data."""

    def __init__(
        self,
        station_id: int,
        api_token: str,
        session: aiohttp.ClientSession = None,
        api: WeatherFlowAPIBase = WeatherFlowAPI(),
    ) -> None:
        """Return data from WeatherFlow API."""
        self._station_id = station_id
        self._api_token = api_token
        self._api = api
        self._json_data = None

        if session:
            self._api.session = session


    def get_forecast(self) -> list[WeatherFlowForecastData]:
        """Return list of forecasts. The first in list are the current one."""
        self._json_data = self._api.get_forecast_api(self._station_id, self._api_token)

        return _get_forecast(self._json_data)

    def get_station(self) -> list[WeatherFlowStationData]:
        """Return list of station information."""
        json_data = self._api.get_station_api(self._station_id, self._api_token)

        return _get_station(json_data)

    async def async_get_forecast(self) -> list[WeatherFlowForecastData]:
        """Return list of forecasts. The first in list are the current one."""
        self._json_data = await self._api.async_get_forecast_api(
            self._station_id, self._api_token
        )

        return _get_forecast(self._json_data)


    async def async_get_station(self) -> list[WeatherFlowStationData]:
        """Return list with Station information."""
        json_data = await self._api.async_get_station_api(
                self._station_id, self._api_token
            )
        return _get_station(json_data)

def _calced_day_values(day_number, hourly_data) -> dict[str, Any]:
    """Calculate values for day by using hourly data."""
    _precipitation: float = 0
    _wind_speed = []
    _wind_bearing = []

    for item in hourly_data:
        if item.get("local_day") == day_number:
            _precipitation += item.get("precip", 0)
            _wind_bearing.append(item.get("wind_direction", 0))
            _wind_speed.append(item.get("wind_avg", 0))

    _sum_wind_speed = sum(_wind_speed) / len(_wind_speed)
    _sum_wind_bearing = sum(_wind_bearing) / len(_wind_bearing)

    return {
        "precipitation": _precipitation,
        "wind_bearing": _sum_wind_bearing,
        "wind_speed": _sum_wind_speed
    }

# pylint: disable=R0914, R0912, W0212, R0915
def _get_forecast(api_result: dict) -> list[WeatherFlowForecastData]:
    """Return WeatherFlowForecast list from API."""

    # Get Current Conditions
    current_conditions: WeatherFlowForecastData = _get_forecast_current(api_result)

    forecasts_daily = []
    forecasts_hourly = []

    # Add daily forecast details
    for item in api_result["forecast"]["daily"]:
        timestamp = item["day_start_local"]
        valid_time = datetime.datetime.fromtimestamp(timestamp)
        condition = item.get("conditions", "Data Error")
        icon = ICON_LIST.get(item["icon"], "exceptional")
        temperature = item.get("air_temp_high", None)
        temp_low = item.get("air_temp_low", None)
        precipitation_probability = item.get("precip_probability", None)
        _calc_values = _calced_day_values(item["day_num"], api_result["forecast"]["hourly"])
        precipitation = _calc_values["precipitation"]
        wind_bearing = _calc_values["wind_bearing"]
        wind_speed = _calc_values["wind_speed"]

        forecast = WeatherFlowForecastDaily(
            valid_time,
            timestamp,
            temperature,
            temp_low,
            condition,
            icon,
            precipitation_probability,
            precipitation,
            wind_bearing,
            wind_speed,
        )
        forecasts_daily.append(forecast)

    current_conditions.forecast_daily = forecasts_daily

    # Add Hourly Forecast
    for item in api_result["forecast"]["hourly"]:
        timestamp = item["time"]
        valid_time = datetime.datetime.fromtimestamp(timestamp)
        condition = item.get("conditions", None)
        icon = ICON_LIST.get(item["icon"], "exceptional")
        temperature = item.get("air_temperature", None)
        apparent_temperature = item.get("feels_like", None)
        precipitation = item.get("precip", None)
        precipitation_probability = item.get("precip_probability", None)
        humidity = item.get("relative_humidity", None)
        pressure = item.get("sea_level_pressure", None)
        uv_index = item.get("uv", None)
        wind_speed = item.get("wind_avg", None)
        wind_gust_speed = item.get("wind_gust", None)
        wind_bearing = item.get("wind_direction", None)

        forecast = WeatherFlowForecastHourly(
            valid_time,
            timestamp,
            temperature,
            apparent_temperature,
            condition,
            icon,
            humidity,
            precipitation,
            precipitation_probability,
            pressure,
            wind_bearing,
            wind_gust_speed,
            wind_speed,
            uv_index,
        )
        forecasts_hourly.append(forecast)

    current_conditions.forecast_hourly = forecasts_hourly

    return current_conditions


# pylint: disable=R0914, R0912, W0212, R0915
def _get_forecast_current(api_result: dict) -> list[WeatherFlowForecastData]:
    """Return WeatherFlowForecast list from API."""

    item = api_result["current_conditions"]

    timestamp = item["time"]
    valid_time = datetime.datetime.fromtimestamp(timestamp)
    condition = item.get("conditions", None)
    icon = ICON_LIST.get(item["icon"], "exceptional")
    temperature = item.get("air_temperature", None)
    dew_point = item.get("dew_point", None)
    apparent_temperature = item.get("feels_like", None)
    precipitation = item.get("precip_accum_local_day", None)
    humidity = item.get("relative_humidity", None)
    pressure = item.get("sea_level_pressure", None)
    uv_index = item.get("uv", None)
    wind_speed = item.get("wind_avg", None)
    wind_gust_speed = item.get("wind_gust", None)
    wind_bearing = item.get("wind_direction", None)

    current_condition = WeatherFlowForecastData(
        valid_time,
        timestamp,
        apparent_temperature,
        condition,
        dew_point,
        humidity,
        icon,
        precipitation,
        pressure,
        temperature,
        uv_index,
        wind_bearing,
        wind_gust_speed,
        wind_speed,
    )

    return current_condition


# pylint: disable=R0914, R0912, W0212, R0915
def _get_station(api_result: dict) -> list[WeatherFlowStationData]:
    """Return WeatherFlowForecast list from API."""

    item = api_result["stations"][0]

    station_name = item.get("name", None)
    latitude = item.get("latitude", None)
    longitude = item.get("longitude", None)
    timezone = item.get("timezone", None)

    station_data = WeatherFlowStationData(
        station_name,
        latitude,
        longitude,
        timezone
    )

    return station_data

