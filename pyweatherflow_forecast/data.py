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
