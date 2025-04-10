"""This module contains the code to get forecast from WeatherFlows Better Forecast API."""

from __future__ import annotations

import abc
import json
import logging
import zoneinfo
import datetime
import tzlocal

from typing import Any
from urllib.request import urlopen, Request

import aiohttp

from .const import (
    ICON_LIST,
    DEFAULT_USER_AGENT,
    WEATHERFLOW_DEVICE_URL,
    WEATHERFLOW_FORECAST_URL,
    WEATHERFLOW_SENSOR_URL,
    WEATHERFLOW_STATION_URL,
)
from .data import (
    WeatherFlowDeviceData,
    WeatherFlowForecastData,
    WeatherFlowForecastDaily,
    WeatherFlowForecastHourly,
    WeatherFlowSensorData,
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
    def api_request( self, url: str) -> dict[str, Any]:
        """Override this."""
        raise NotImplementedError(
            "users must define api_request to use this base class"
        )

    @abc.abstractmethod
    async def async_api_request( self, url: str) -> dict[str, Any]:
        """Override this."""
        raise NotImplementedError(
            "users must define async_api_request to use this base class"
        )

class WeatherFlowAPI(WeatherFlowAPIBase):
    """Default implementation for WeatherFlow api."""

    def __init__(self) -> None:
        """Init the API with or without session."""
        self.session = None
        self._user_agent = None

    @property
    def user_agent(self) -> str | None:
        """Return the current User-Agent string."""
        return self._user_agent

    @user_agent.setter
    def user_agent(self, value: str) -> None:
        """Set the User-Agent string to be used in requests."""
        self._user_agent = value

    def api_request(self, url: str) -> dict[str, Any]:
        """Return data from API."""
        _LOGGER.debug("URL: %s", url)

        headers = {}
        if self._user_agent:
            headers['User-Agent'] = self._user_agent
        else:
            headers['User-Agent'] = DEFAULT_USER_AGENT

        request = Request(url, headers=headers)
        response = urlopen(request)
        data = response.read().decode("utf-8")
        json_data = json.loads(data)

        return json_data

    async def async_api_request(self, url: str) -> dict[str, Any]:
        """Get data from WeatherFlow API."""

        _LOGGER.debug("URL CALLED: %s", url)

        is_new_session = False
        if self.session is None:
            self.session = aiohttp.ClientSession()
            is_new_session = True

        headers = {}
        if self._user_agent:
            headers['User-Agent'] = self._user_agent
        else:
            headers['User-Agent'] = DEFAULT_USER_AGENT

        async with self.session.get(url, headers=headers) as response:
            if response.status != 200:
                if is_new_session:
                    await self.session.close()
                if response.status == 400:
                    raise WeatherFlowForecastBadRequest(
                        "400 BAD_REQUEST: Requests is invalid in some way (invalid dates, bad location parameter etc)."
                    )
                if response.status == 401:
                    raise WeatherFlowForecastUnauthorized(
                        "401 UNAUTHORIZED: The API token is incorrect or your account status is inactive or disabled."
                    )
                if response.status == 404:
                    raise WeatherFlowForecastWongStationId(
                        "404 NOT FOUND: The ID of the Station or Device cannot be found."
                    )
                if response.status == 500:
                    raise WeatherFlowForecastInternalServerError(
                        "500 INTERNAL_SERVER_ERROR: WeatherFlow servers encounter an unexpected error."
                    )

            data = await response.text()
            if is_new_session:
                await self.session.close()

            json_data = json.loads(data)

            return json_data


class WeatherFlow:
    """Class that uses the Better Forecast API from WeatherFlow to retreive forecast data."""

    def __init__(
        self,
        station_id: int,
        api_token: str,
        forecast_hours: int = 72,
        session: aiohttp.ClientSession = None,
        elevation = None,
        api: WeatherFlowAPIBase = WeatherFlowAPI(),
    ) -> None:
        """Return data from WeatherFlow API."""
        self._station_id = station_id
        self._api_token = api_token
        self._forecast_hours = forecast_hours
        self._elevation = elevation
        self._api = api
        self._device_id = None
        self._tempest_device = False
        self._json_data = None
        self._station_data: WeatherFlowStationData = None
        self._device_data: WeatherFlowDeviceData = None
        self._voltage: float = None

        if session:
            self._api.session = session

    @property
    def user_agent(self) -> str | None:
        """Return the User-Agent string used by the API client."""
        if isinstance(self._api, WeatherFlowAPI):
            return self._api.user_agent
        return None

    @user_agent.setter
    def user_agent(self, value: str) -> None:
        """Set the User-Agent string for the API client."""
        if isinstance(self._api, WeatherFlowAPI):
            self._api.user_agent = value

    def get_forecast(self) -> list[WeatherFlowForecastData]:
        """Return list of forecasts. The first in list are the current one."""
        api_url = f"{WEATHERFLOW_FORECAST_URL}{self._station_id}&api_key={self._api_token}"
        self._json_data = self._api.api_request(api_url)

        return _get_forecast(self._json_data, self._forecast_hours)

    def get_station(self) -> list[WeatherFlowStationData]:
        """Return list of station information."""
        station_url = f"{WEATHERFLOW_STATION_URL}{self._station_id}?api_key={self._api_token}"
        json_data = self._api.api_request(station_url)
        return _get_station(json_data)

    def fetch_sensor_data(self, voltage: float = None) -> list[WeatherFlowSensorData]:
        """Return list of sensor data."""
        device_data = None
        sensor_data = None

        if self._device_id is None and not self._tempest_device:
            station_url = f"{WEATHERFLOW_STATION_URL}{self._station_id}?api_key={self._api_token}"
            json_station_data = self._api.api_request(station_url)
            station_data: WeatherFlowStationData = _get_station(json_station_data)
            self._device_id = station_data.device_id
            self._station_name = station_data.station_name
            self._tempest_device = False if self._device_id is None else True

        if self._device_id is not None:
            _device_id = station_data.device_id
            device_url = f"{WEATHERFLOW_DEVICE_URL}{_device_id}?api_key={self._api_token}"
            json_device_data = self._api.api_request(device_url)
            device_data: WeatherFlowDeviceData = _get_device_data(json_device_data, _device_id)

        if device_data is not None or not self._tempest_device:
            _precipitation_type = device_data.precipitation_type if self._tempest_device else None
            _voltage = device_data.voltage if self._tempest_device else None
            api_url = f"{WEATHERFLOW_SENSOR_URL}{self._station_id}?api_key={self._api_token}"
            json_data = self._api.api_request(api_url)
            sensor_data = _get_sensor_data(json_data, self._elevation, _voltage, _precipitation_type, self._station_name)

        return sensor_data

    async def async_fetch_sensor_data(self) -> list[WeatherFlowSensorData]:
        """Return sensor data from API."""
        device_data = None
        sensor_data = None

        if self._device_id is None and not self._tempest_device:
            station_url = f"{WEATHERFLOW_STATION_URL}{self._station_id}?api_key={self._api_token}"
            json_station_data = await self._api.async_api_request(station_url)
            station_data: WeatherFlowStationData = _get_station(json_station_data)
            self._device_id = station_data.device_id
            self._station_name = station_data.station_name
            self._tempest_device = False if self._device_id is None else True

        if self._device_id is not None:
            device_url = f"{WEATHERFLOW_DEVICE_URL}{self._device_id}?api_key={self._api_token}"
            json_device_data = await self._api.async_api_request(device_url)
            device_data: WeatherFlowDeviceData = _get_device_data(json_device_data, self._device_id)

        if device_data is not None or not self._tempest_device:
            _precipitation_type = device_data.precipitation_type if self._tempest_device else None
            _voltage = device_data.voltage if self._tempest_device else None
            api_url = f"{WEATHERFLOW_SENSOR_URL}{self._station_id}?api_key={self._api_token}"
            json_data = await self._api.async_api_request(api_url)
            sensor_data = _get_sensor_data(json_data, self._elevation, _voltage, _precipitation_type, self._station_name)

        return sensor_data

    async def async_get_forecast(self) -> list[WeatherFlowForecastData]:
        """Return list of forecasts. The first in list are the current one."""
        api_url = f"{WEATHERFLOW_FORECAST_URL}{self._station_id}&api_key={self._api_token}"
        self._json_data = await self._api.async_api_request(api_url)

        return _get_forecast(self._json_data, self._forecast_hours)

    async def async_get_station(self) -> list[WeatherFlowStationData]:
        """Return list with Station information."""
        api_url = f"{WEATHERFLOW_STATION_URL}{self._station_id}?api_key={self._api_token}"

        json_data = await self._api.async_api_request(api_url)
        station_data = _get_station(json_data)
        self._station_data = station_data
        return station_data


def _get_offline_sensor_data(voltage: float) -> list[WeatherFlowSensorData]:
    """Return list of sensor data from offline file."""

    sensor_data = WeatherFlowSensorData(
        False,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        voltage,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
    )

    return sensor_data

def _calced_day_values(day_number, hourly_data) -> dict[str, Any]:
    """Calculate values for day by using hourly data."""
    _precipitation: float = 0
    _wind_speed = []
    _wind_bearing = []
    _wind_gust = []

    for item in hourly_data:
        if item.get("local_day") == day_number:
            _precipitation += item.get("precip", 0)
            _wind_bearing.append(item.get("wind_direction", 0))
            _wind_speed.append(item.get("wind_avg", 0))
            _wind_gust.append(item.get("wind_gust", 0))

    _sum_wind_speed = sum(_wind_speed) / len(_wind_speed) if _wind_speed else 0
    _sum_wind_bearing = sum(_wind_bearing) / len(_wind_bearing) if _wind_bearing else 0
    _max_wind_gust = max(_wind_gust) if _wind_gust else 0

    return {
        "precipitation": _precipitation,
        "wind_bearing": _sum_wind_bearing,
        "wind_speed": _sum_wind_speed,
        "wind_gust": _max_wind_gust,
    }


def _align_source_to_local_time(timestamp, source_timezone):
    """
    Converts a timestamp and forces the output date to match the source date in the local timezone.
    Uses tzlocal for reliable timezone detection (using zoneinfo).

    This prevents forecast data from being displayed with a date earlier than the current date.
    """
    try:
        source_tz = zoneinfo.ZoneInfo(source_timezone)
        local_tz = tzlocal.get_localzone()  # Get the IANA timezone

        source_dt = datetime.datetime.fromtimestamp(timestamp, tz=source_tz)
        target_dt_temp = source_dt.astimezone(local_tz)

        # Get the date from the source timezone
        source_date = source_dt.date()

        # Force the date in the local timezone to match the source date
        target_dt = datetime.datetime(
            source_date.year,
            source_date.month,
            source_date.day,
            target_dt_temp.hour,
            target_dt_temp.minute,
            target_dt_temp.second,
            tzinfo=local_tz,
        )

    except zoneinfo.ZoneInfoNotFoundError as e:
        print(f"Error: Timezone not found - {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    return target_dt, int(target_dt.timestamp())

# pylint: disable=R0914, R0912, W0212, R0915
def _get_forecast(api_result: dict, forecast_hours: int) -> list[WeatherFlowForecastData]:
    """Return WeatherFlowForecast list from API."""

    # Get Current Conditions
    current_conditions: WeatherFlowForecastData = _get_forecast_current(api_result)

    forecasts_daily = []
    forecasts_hourly = []

    _LOGGER.info("API RESULT: %s", api_result)

    source_tz = zoneinfo.ZoneInfo(api_result["timezone"])
    print("SOURCE TZ: ", source_tz)

    # Add daily forecast details
    for item in api_result["forecast"]["daily"]:
        timestamp = item["day_start_local"]
        adj_dt, adj_ts = _align_source_to_local_time(timestamp, api_result["timezone"])
        condition = item.get("conditions", "Data Error")
        icon_string = item["icon"]
        icon = ICON_LIST.get(icon_string, "unknown")
        temperature = item.get("air_temp_high", None)
        temp_low = item.get("air_temp_low", None)
        precipitation_probability = item.get("precip_probability", None)
        precipitation_icon = item.get("precip_icon", None)
        precipitation_type = item.get("precip_type", None)
        _calc_values = _calced_day_values(item["day_num"], api_result["forecast"]["hourly"])
        precipitation = _calc_values["precipitation"]
        wind_bearing = _calc_values["wind_bearing"]
        wind_speed = _calc_values["wind_speed"]
        wind_gust = _calc_values["wind_gust"]

        forecast = WeatherFlowForecastDaily(
            adj_dt,
            adj_ts,
            temperature,
            temp_low,
            condition,
            icon,
            precipitation_probability,
            precipitation,
            precipitation_icon,
            precipitation_type,
            wind_bearing,
            wind_speed,
            wind_gust,
        )
        forecasts_daily.append(forecast)

    current_conditions.forecast_daily = forecasts_daily

    # Add Hourly Forecast
    _hour_counter = 1
    for item in api_result["forecast"]["hourly"]:
        if _hour_counter > forecast_hours:
            break

        timestamp = item["time"]
        valid_time = datetime.datetime.fromtimestamp(timestamp)
        condition = item.get("conditions", None)
        icon = ICON_LIST.get(item["icon"], "unknown")
        temperature = item.get("air_temperature", None)
        apparent_temperature = item.get("feels_like", None)
        precipitation = item.get("precip", None)
        precipitation_probability = item.get("precip_probability", None)
        precipitation_icon = item.get("precip_icon", None)
        precipitation_type = item.get("precip_type", None)
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
            precipitation_icon,
            precipitation_type,
            pressure,
            wind_bearing,
            wind_gust_speed,
            wind_speed,
            uv_index,
        )
        forecasts_hourly.append(forecast)
        _hour_counter += 1

    current_conditions.forecast_hourly = forecasts_hourly

    return current_conditions


# pylint: disable=R0914, R0912, W0212, R0915
def _get_forecast_current(api_result: dict) -> list[WeatherFlowForecastData]:
    """Return WeatherFlowForecast list from API."""

    item = api_result["current_conditions"]
    timestamp = item.get("time", None)
    valid_time = datetime.datetime.fromtimestamp(timestamp) if timestamp is not None else datetime.datetime.now()
    condition = item.get("conditions", None)
    icon = ICON_LIST.get(item["icon"], "unknown")
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

    if len(api_result["stations"]) == 0:
        raise WeatherFlowForecastWongStationId("Station ID does not exist. Please check you are not using Device ID")

    item = api_result["stations"][0]

    station_name = item.get("name", None)
    latitude = item.get("latitude", None)
    longitude = item.get("longitude", None)
    timezone = item.get("timezone", None)
    device_id = None
    firmware_revision = None
    serial_number = None
    for device in item["devices"]:
        if device.get("device_type", None) == "ST":
            device_id = device.get("device_id", None)
            firmware_revision = device.get("firmware_revision", None)
            serial_number = device.get("serial_number", None)
            break

    station_data = WeatherFlowStationData(
        station_name,
        latitude,
        longitude,
        timezone,
        device_id,
        firmware_revision,
        serial_number,
    )

    return station_data


# pylint: disable=R0914, R0912, W0212, R0915
def _get_sensor_data(api_result: dict, elevation: float, voltage: float, precipitation_type: int, station_name: str) -> list[WeatherFlowSensorData]:
    """Return WeatherFlowSensorData list from API."""

    _LOGGER.debug("ELEVATION: %s", elevation)

    if len(api_result["obs"]) == 0:
        _LOGGER.warning("Weather Station either is offline or no recent observations.")
        return _get_offline_sensor_data(voltage=voltage)

    item = api_result["obs"][0]

    air_density = item.get("air_density", None)
    air_temperature = item.get("air_temperature", None)
    barometric_pressure = item.get("barometric_pressure", None)
    brightness = item.get("brightness", None)
    delta_t = item.get("delta_t", None)
    dew_point = item.get("dew_point", None)
    feels_like = item.get("feels_like", None)
    heat_index = item.get("heat_index", None)
    lightning_strike_count = item.get("lightning_strike_count", None)
    lightning_strike_count_last_1hr = item.get("lightning_strike_count_last_1hr", None)
    lightning_strike_count_last_3hr = item.get("lightning_strike_count_last_3hr", None)
    lightning_strike_last_distance = item.get("lightning_strike_last_distance", None)
    lightning_strike_last_epoch = item.get("lightning_strike_last_epoch", None)
    precip = item.get("precip", None)
    precip_accum_last_1hr = item.get("precip_accum_last_1hr", None)
    precip_accum_local_day = item.get("precip_accum_local_day", None)
    precip_accum_local_yesterday = item.get("precip_accum_local_yesterday", None)
    precip_minutes_local_day = item.get("precip_minutes_local_day", None)
    precip_minutes_local_yesterday = item.get("precip_minutes_local_yesterday", None)
    pressure_trend = item.get("pressure_trend", None)
    relative_humidity = item.get("relative_humidity", None)
    sea_level_pressure = item.get("sea_level_pressure", None)
    solar_radiation = item.get("solar_radiation", None)
    station_pressure = item.get("station_pressure", None)
    timestamp = item.get("timestamp", None)
    uv = item.get("uv", None)
    wet_bulb_globe_temperature = item.get("wet_bulb_globe_temperature", None)
    wet_bulb_temperature = item.get("wet_bulb_temperature", None)
    wind_avg = item.get("wind_avg", None)
    wind_chill = item.get("wind_chill", None)
    wind_direction = item.get("wind_direction", None)
    wind_gust = item.get("wind_gust", None)
    wind_lull = item.get("wind_lull", None)
    precip_accum_local_day_final = item.get("precip_accum_local_day_final", None)
    precip_accum_local_yesterday_final = item.get("precip_accum_local_yesterday_final", None)
    precip_minutes_local_day_final = item.get("precip_minutes_local_day_final", None)
    precip_minutes_local_yesterday_final = item.get("precip_minutes_local_yesterday_final", None)

    sensor_data = WeatherFlowSensorData(
        True,
        air_density,
        air_temperature,
        barometric_pressure,
        brightness,
        delta_t,
        dew_point,
        feels_like,
        heat_index,
        lightning_strike_count,
        lightning_strike_count_last_1hr,
        lightning_strike_count_last_3hr,
        lightning_strike_last_distance,
        lightning_strike_last_epoch,
        precip,
        precip_accum_last_1hr,
        precip_accum_local_day,
        precip_accum_local_yesterday,
        precip_minutes_local_day,
        precip_minutes_local_yesterday,
        precipitation_type,
        pressure_trend,
        relative_humidity,
        sea_level_pressure,
        solar_radiation,
        station_pressure,
        timestamp,
        uv,
        voltage,
        wet_bulb_globe_temperature,
        wet_bulb_temperature,
        wind_avg,
        wind_chill,
        wind_direction,
        wind_gust,
        wind_lull,
        precip_accum_local_day_final,
        precip_accum_local_yesterday_final,
        precip_minutes_local_day_final,
        precip_minutes_local_yesterday_final,
        elevation,
        station_name,
    )

    return sensor_data

# pylint: disable=R0914, R0912, W0212, R0915
def _get_device_data(api_result: dict, device_id: int) -> float:
    """Return WeatherFlow Device Voltage from API."""

    precipitation_type = None if api_result is None else api_result["obs"][0][13]
    voltage = None if api_result is None else api_result["obs"][0][16]

    device_data = WeatherFlowDeviceData(
        device_id,
        voltage,
        precipitation_type,
    )

    return device_data