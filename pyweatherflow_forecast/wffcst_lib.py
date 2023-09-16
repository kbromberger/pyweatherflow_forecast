"""
This module contains the code to get forecast from
WeatherFlows Better Forecast API.
"""
from __future__ import annotations

import abc
import copy
import datetime
import json
import logging

from collections import OrderedDict
from typing import List, Any, Dict
from urllib.request import urlopen

import aiohttp

from .const import ICON_LIST, WEATHERFLOW_FORECAST_URL
from .data import WeatherFlowForecastDaily, WeatherFlowForecastHourly

_LOGGER = logging.getLogger(__name__)
# Timezone
UTC = datetime.timezone.utc

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
        self._json_data = None

        if session:
            self._api.session = session


    def get_forecast(self) -> List[WeatherFlowForecastDaily]:
        """
        Returns a list of forecasts. The first in list are the current one
        """
        if self._json_data is None or not validate_data(self._json_data):
            self._json_data = self._api.get_forecast_api(self._station_id, self._api_token)
        return _get_forecast(self._json_data)

    def get_forecast_hour(self) -> List[WeatherFlowForecastHourly]:
        """
        Returns a list of forecasts by hour. The first in list are the current one
        """
        if self._json_data is None or not validate_data(self._json_data):
            self._json_data = self._api.get_forecast_api(self._station_id, self._api_token)
        return _get_forecast_hour(self._json_data)

    async def async_get_forecast(self) -> List[WeatherFlowForecastDaily]:
        """
        Returns a list of forecasts. The first in list are the current one
        """
        json_data = await self._api.async_get_forecast_api(
            self._station_id, self._api_token
        )
        return _get_forecast(json_data)

    async def async_get_forecast_hour(self) -> List[WeatherFlowForecastHourly]:
        """
        Returns a list of forecasts by hour. The first in list are the current one
        """
        json_data = await self._api.async_get_forecast_api(
            self._station_id, self._api_token
        )
        return _get_forecast_hour(json_data)

def validate_data(json_data) -> bool:
    """Returns true if data is valid else false."""
    data_time = json_data["current_conditions"]["time"]
    data_time_obj = datetime.datetime.fromtimestamp(data_time)
    now = datetime.datetime.now()
    delta = now - data_time_obj
    minutes = delta.seconds / 60
    if minutes > 30:
        return False
    return True


# pylint: disable=R0914, R0912, W0212, R0915
def _get_forecast(api_result: dict) -> List[WeatherFlowForecastDaily]:
    """Converts results from API to WeatherFlowForecast list"""
    forecasts = []

    for item in api_result["forecast"]["daily"]:
        valid_time = datetime.datetime.utcfromtimestamp(item["day_start_local"]).replace(tzinfo=UTC)
        condition = item["conditions"]
        icon = ICON_LIST.get(item["icon"], "exceptional")
        temperature = item["air_temp_high"]
        temp_low = item["air_temp_low"]
        precipitation_probability = item["precip_probability"]

        forecast = WeatherFlowForecastDaily(
            valid_time,
            temperature,
            temp_low,
            condition,
            icon,
            precipitation_probability,
        )
        forecasts.append(forecast)

    return forecasts


def _get_forecast_hour(api_result: dict) -> List[WeatherFlowForecastHourly]:
    """Converts results from API to WeatherFlowForecast list"""
    forecasts = []

    for item in api_result["forecast"]["hourly"]:
        valid_time = datetime.datetime.utcfromtimestamp(item["time"]).replace(tzinfo=UTC)
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
        forecasts.append(forecast)

    return forecasts


# pylint: disable=R0914, R0912, W0212, R0915
def _get_all_forecast_from_api(api_result: dict) -> OrderedDict:
    """Converts results from API to WeatherFlowForecast list"""

    # Total time in hours since last forecast
    total_hours_last_forecast = 1.0

    # Last forecast time
    last_time = None

    # Timezone
    UTC = datetime.timezone.utc

    # Need the ordered dict to get
    # the days in order in next stage
    forecasts_ordered = OrderedDict()

    for forecast in api_result["forecast"]["daily"]:
        valid_time = datetime.datetime.utcfromtimestamp(forecast["day_start_local"]).replace(tzinfo=UTC)
        condition = forecast["conditions"]
        icon = forecast["icon"]
        temperature = forecast["air_temp_high"]
        temp_low = forecast["air_temp_low"]

    # Get the parameters
    # for forecast in api_result["timeSeries"]:
    #     valid_time = datetime.strptime(forecast["validTime"], "%Y-%m-%dT%H:%M:%SZ")
    #     for param in forecast["parameters"]:
    #         if param["name"] == "t":
    #             temperature = float(param["values"][0])  # Celcisus
    #         elif param["name"] == "r":
    #             humidity = int(param["values"][0])  # Percent
    #         elif param["name"] == "msl":
    #             pressure = int(param["values"][0])  # hPa
    #         elif param["name"] == "tstm":
    #             thunder = int(param["values"][0])  # Percent
    #         elif param["name"] == "tcc_mean":
    #             octa = int(param["values"][0])  # Cloudiness in octas
    #             if 0 <= octa <= 8:  # Between 0 -> 8
    #                 cloudiness = round(100 * octa / 8)  # Convert octas to percent
    #             else:
    #                 cloudiness = 100  # If not determined use 100%
    #         elif param["name"] == "Wsymb2":
    #             symbol = int(param["values"][0])  # category
    #         elif param["name"] == "pcat":
    #             precipitation = int(param["values"][0])  # percipitation
    #         elif param["name"] == "pmean":
    #             mean_precipitation = float(param["values"][0])  # mean_percipitation
    #         elif param["name"] == "ws":
    #             wind_speed = float(param["values"][0])  # wind speed
    #         elif param["name"] == "wd":
    #             wind_direction = int(param["values"][0])  # wind direction
    #         elif param["name"] == "vis":
    #             horizontal_visibility = float(param["values"][0])  # Visibility
    #         elif param["name"] == "gust":
    #             wind_gust = float(param["values"][0])  # wind gust speed

    #     rounded_temp = int(round(temperature))

        if last_time is not None:
            total_hours_last_forecast = (valid_time - last_time).seconds / 60 / 60

        # Total precipitation, have to calculate with the nr of
        # hours since last forecast to get correct total value
        # total_precipitation = round(mean_precipitation * total_hours_last_forecast, 2)

        forecast = WeatherFlowForecast(
            valid_time,
            temperature,
            temp_low,
            condition,
            icon,
            humidity=0,
            apparent_temperature=0,
            precipitation=0,
            precipitation_probability=0,
            pressure=0,
            wind_bearing=0,
            wind_gust_speed=0,
            wind_speed=0,
            uv_index=0,
        )

        if valid_time.day not in forecasts_ordered:
            # add a new list
            forecasts_ordered[valid_time.day] = []

        forecasts_ordered[valid_time.day].append(forecast)

        last_time = valid_time

    return forecasts_ordered


# pylint: disable=R0914, R0912, W0212, R0915
def _get_all_forecast_from_api_org(api_result: dict) -> OrderedDict:
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
