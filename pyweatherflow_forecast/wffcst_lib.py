"""
This module contains the code to get forecast from
WeatherFlows Better Forecast API.
"""
from __future__ import annotations

import abc
import copy
import json

from collections import OrderedDict
from datetime import datetime
from typing import List, Any, Dict
from urllib.request import urlopen

import aiohttp

from .const import WEATHERFLOW_FORECAST_URL


class WeatherFlowForecastException(Exception):
    """Exception thrown if failing to access API"""

class WeatherFlowForecast:
    """Class to hold forecast data."""
        # pylint: disable=R0913, R0902, R0914
    def __init__(
        self,
        temperature: float,
        temp_low: float,
        condition: str,
        humidity: int,
        apparent_temperature: float,
        precipitation: float,
        precipitation_probability: int,
        pressure: float,
        wind_bearing: float,
        wind_gust_speed: int,
        wind_speed: int,
        uv_index: float,
        valid_time: datetime,
    ) -> None:
        """Constructor"""
        self._temperature = temperature
        self._temp_low = temp_low
        self._condition = condition
        self._humidity = humidity
        self._apparent_temperature = apparent_temperature
        self._precipitation = precipitation
        self._precipitation_probability = precipitation_probability
        self._pressure = pressure
        self._wind_bearing = wind_bearing
        self._wind_gust_speed = wind_gust_speed
        self._wind_speed = wind_speed
        self._uv_index = uv_index
        self._valid_time = valid_time

    @property
    def temperature(self) -> float:
        """Air temperature (Celcius)"""
        return self._temperature

    @property
    def temp_low(self) -> float:
        """Air temperature min during the day (Celcius)"""
        return self._temp_low

    @property
    def condition(self) -> str:
        """Weather condition symbol."""
        return self._condition

    @property
    def humidity(self) -> int:
        """Humidity (%)."""
        return self._humidity

    @property
    def apparent_temperature(self) -> float:
        """Feels like temperature (Celcius)."""
        return self._apparent_temperature

    @property
    def precipitation(self) -> float:
        """Precipitation (mm)."""
        return self._precipitation

    @property
    def precipitation_probability (self) -> int:
        """Posobility of Precipiation (%)."""
        return self._precipitation_probability

    @property
    def pressure(self) -> float:
        """Sea Level Pressure (MB)"""
        return self._pressure

    @property
    def wind_bearing(self) -> float:
        """Wind bearing (degrees)"""
        return self._wind_bearing

    @property
    def wind_gust_speed(self) -> float:
        """Wind gust (m/s)"""
        return self._wind_gust_speed

    @property
    def wind_speed(self) -> float:
        """Wind speed (m/s)"""
        return self._wind_speed

    @property
    def uv_index(self) -> float:
        """UV Index"""
        return self._uv_index

    @property
    def valid_time(self) -> datetime:
        """Valid time"""
        return self._valid_time

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


class WeatherFlow:
    """
    Class that uses the Better Forecast API from WeatherFlow to retreive
    forecast data for daily and hourly.
    """

    def __init__(
        self,
        station_id: int,
        api_token: str,
        session: aiohttp.ClientSession = None,
        api: WeatherFlowAPIBase = WeatherFlowAPI(),
    ) -> None:
        self._station_id = station_id
        self._api_token = api_token
        self._api = api

        if session:
            self._api.session = session


    def get_forecast(self) -> List[WeatherFlowForecast]:
        """
        Returns a list of forecasts. The first in list are the current one
        """
        json_data = self._api.get_forecast_api(self._station_id, self._api_token)
        return _get_forecast(json_data)

    def get_forecast_hour(self) -> List[WeatherFlowForecast]:
        """
        Returns a list of forecasts by hour. The first in list are the current one
        """
        json_data = self._api.get_forecast_api(self._station_id, self._api_token)
        return _get_forecast_hour(json_data)

    async def async_get_forecast(self) -> List[WeatherFlowForecast]:
        """
        Returns a list of forecasts. The first in list are the current one
        """
        json_data = await self._api.async_get_forecast_api(
            self._station_id, self._api_token
        )
        return _get_forecast(json_data)

    async def async_get_forecast_hour(self) -> List[WeatherFlowForecast]:
        """
        Returns a list of forecasts by hour. The first in list are the current one
        """
        json_data = await self._api.async_get_forecast_api(
            self._station_id, self._api_token
        )
        return _get_forecast_hour(json_data)


# pylint: disable=R0914, R0912, W0212, R0915
def _get_forecast(api_result: dict) -> List[WeatherFlowForecast]:
    """Converts results from API to WeatherFlowForecast list"""
    forecasts = []

    # Need the ordered dict to get
    # the days in order in next stage
    forecasts_ordered = OrderedDict()

    forecasts_ordered = _get_all_forecast_from_api(api_result)

    # Used to calc the daycount
    day_nr = 1

    for day in forecasts_ordered:
        forecasts_day = forecasts_ordered[day]

        if day_nr == 1:
            # Add the most recent forecast
            forecasts.append(copy.deepcopy(forecasts_day[0]))

        total_precipitation = float(0.0)
        forecast_temp_max = -100.0
        forecast_temp_min = 100.0
        forecast = None
        for forcast_day in forecasts_day:
            temperature = forcast_day.temperature
            if forecast_temp_min > temperature:
                forecast_temp_min = temperature
            if forecast_temp_max < temperature:
                forecast_temp_max = temperature

            if forcast_day.valid_time.hour == 12:
                forecast = copy.deepcopy(forcast_day)

            total_precipitation = total_precipitation + forcast_day._total_precipitation

        if forecast is None:
            # We passed 12 noon, set to current
            forecast = forecasts_day[0]

        forecast._temperature_max = forecast_temp_max
        forecast._temperature_min = forecast_temp_min
        forecast._total_precipitation = total_precipitation
        forecast._mean_precipitation = total_precipitation / 24
        forecasts.append(forecast)
        day_nr = day_nr + 1

    return forecasts


def _get_forecast_hour(api_result: dict) -> List[WeatherFlowForecast]:
    """Converts results from API to WeatherFlowForecast list"""
    forecasts = []

    # Need the ordered dict to get
    # the days in order in next stage
    forecasts_ordered = OrderedDict()

    forecasts_ordered = _get_all_forecast_from_api(api_result)

    for day in forecasts_ordered:
        for forecast_hour in forecasts_ordered[day]:
            forecast = forecast_hour
            forecast._total_precipitation = forecast._mean_precipitation

            forecasts.append(forecast)

    return forecasts


# pylint: disable=R0914, R0912, W0212, R0915


def _get_all_forecast_from_api(api_result: dict) -> OrderedDict:
    """Converts results from API to WeatherFlowForecast list"""
    # Total time in hours since last forecast
    total_hours_last_forecast = 1.0

    # Last forecast time
    last_time = None

    # Need the ordered dict to get
    # the days in order in next stage
    forecasts_ordered = OrderedDict()

    # Get the parameters
    for forecast in api_result["timeSeries"]:
        valid_time = datetime.strptime(forecast["validTime"], "%Y-%m-%dT%H:%M:%SZ")
        for param in forecast["parameters"]:
            if param["name"] == "t":
                temperature = float(param["values"][0])  # Celcisus
            elif param["name"] == "r":
                humidity = int(param["values"][0])  # Percent
            elif param["name"] == "msl":
                pressure = int(param["values"][0])  # hPa
            elif param["name"] == "tstm":
                thunder = int(param["values"][0])  # Percent
            elif param["name"] == "tcc_mean":
                octa = int(param["values"][0])  # Cloudiness in octas
                if 0 <= octa <= 8:  # Between 0 -> 8
                    cloudiness = round(100 * octa / 8)  # Convert octas to percent
                else:
                    cloudiness = 100  # If not determined use 100%
            elif param["name"] == "Wsymb2":
                symbol = int(param["values"][0])  # category
            elif param["name"] == "pcat":
                precipitation = int(param["values"][0])  # percipitation
            elif param["name"] == "pmean":
                mean_precipitation = float(param["values"][0])  # mean_percipitation
            elif param["name"] == "ws":
                wind_speed = float(param["values"][0])  # wind speed
            elif param["name"] == "wd":
                wind_direction = int(param["values"][0])  # wind direction
            elif param["name"] == "vis":
                horizontal_visibility = float(param["values"][0])  # Visibility
            elif param["name"] == "gust":
                wind_gust = float(param["values"][0])  # wind gust speed

        rounded_temp = int(round(temperature))

        if last_time is not None:
            total_hours_last_forecast = (valid_time - last_time).seconds / 60 / 60

        # Total precipitation, have to calculate with the nr of
        # hours since last forecast to get correct total value
        total_precipitation = round(mean_precipitation * total_hours_last_forecast, 2)

        forecast = WeatherFlowForecast(
            rounded_temp,
            rounded_temp,
            rounded_temp,
            humidity,
            pressure,
            thunder,
            cloudiness,
            precipitation,
            wind_direction,
            wind_speed,
            horizontal_visibility,
            wind_gust,
            round(mean_precipitation, 1),
            total_precipitation,
            symbol,
            valid_time,
        )

        if valid_time.day not in forecasts_ordered:
            # add a new list
            forecasts_ordered[valid_time.day] = []

        forecasts_ordered[valid_time.day].append(forecast)

        last_time = valid_time

    return forecasts_ordered
