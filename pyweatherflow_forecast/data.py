"""Holds the Data Calsses for WeatherFlow Forecast Wrapper"""

from __future__ import annotations
from datetime import datetime

class WeatherFlowForecastDaily:
    """Class to hold daily forecast data."""
        # pylint: disable=R0913, R0902, R0914
    def __init__(
        self,
        valid_time: datetime,
        temperature: float,
        temp_low: float,
        condition: str,
        icon: str,
        precipitation_probability: int,
    ) -> None:
        """Constructor"""
        self._valid_time = valid_time
        self._temperature = temperature
        self._temp_low = temp_low
        self._condition = condition
        self._icon = icon
        self._precipitation_probability = precipitation_probability

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
        """Weather condition text."""
        return self._condition

    @property
    def icon(self) -> str:
        """Weather condition symbol."""
        return self._icon

    @property
    def precipitation_probability (self) -> int:
        """Posobility of Precipiation (%)."""
        return self._precipitation_probability

    @property
    def valid_time(self) -> datetime:
        """Valid time"""
        return self._valid_time


class WeatherFlowForecastHourly:
    """Class to hold hourly forecast data."""
        # pylint: disable=R0913, R0902, R0914
    def __init__(
        self,
        valid_time: datetime,
        temperature: float,
        apparent_temperature: float,
        condition: str,
        icon: str,
        humidity: int,
        precipitation: float,
        precipitation_probability: int,
        pressure: float,
        wind_bearing: float,
        wind_gust_speed: int,
        wind_speed: int,
        uv_index: float,
    ) -> None:
        """Constructor"""
        self._valid_time = valid_time
        self._temperature = temperature
        self._apparent_temperature = apparent_temperature
        self._condition = condition
        self._icon = icon
        self._humidity = humidity
        self._precipitation = precipitation
        self._precipitation_probability = precipitation_probability
        self._pressure = pressure
        self._wind_bearing = wind_bearing
        self._wind_gust_speed = wind_gust_speed
        self._wind_speed = wind_speed
        self._uv_index = uv_index

    @property
    def temperature(self) -> float:
        """Air temperature (Celcius)"""
        return self._temperature

    @property
    def condition(self) -> str:
        """Weather condition text."""
        return self._condition

    @property
    def icon(self) -> str:
        """Weather condition symbol."""
        return self._icon

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
