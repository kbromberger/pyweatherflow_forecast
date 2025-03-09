"""System Wide constants for WeatherFlow Forecast Wrapper."""
from __future__ import annotations

CACHE_MINUTES = 30

FORECAST_TYPE_DAILY = 0
FORECAST_TYPE_HOURLY = 1

WEATHERFLOW_BASE_URL = "https://swd.weatherflow.com/swd/rest"
WEATHERFLOW_DEVICE_URL = f"{WEATHERFLOW_BASE_URL}/observations/device/"
WEATHERFLOW_FORECAST_URL = f"{WEATHERFLOW_BASE_URL}/better_forecast?station_id="
WEATHERFLOW_SENSOR_URL = f"{WEATHERFLOW_BASE_URL}/observations/station/"
WEATHERFLOW_STATION_URL = f"{WEATHERFLOW_BASE_URL}/stations/"

ICON_LIST = {
    "clear-day": "sunny",
    "cc-clear-day": "sunny",
    "clear-night": "clear-night",
    "cc-clear-night": "clear-night",
    "cloudy": "cloudy",
    "cc-cloudy": "cloudy",
    "foggy": "fog",
    "cc-foggy": "fog",
    "partly-cloudy-day": "partlycloudy",
    "cc-partly-cloudy-day": "partlycloudy",
    "partly-cloudy-night": "partlycloudy",
    "cc-partly-cloudy-night": "partlycloudy",
    "possibly-rainy-day": "rainy",
    "cc-possibly-rainy-day": "rainy",
    "possibly-rainy-night": "rainy",
    "cc-possibly-rainy-night": "rainy",
    "possibly-sleet-day": "snowy-rainy",
    "cc-possibly-sleet-day": "snowy-rainy",
    "possibly-sleet-night": "snowy-rainy",
    "cc-possibly-sleet-night": "snowy-rainy",
    "possibly-snow-day": "snowy",
    "cc-possibly-snow-day": "snowy",
    "possibly-snow-night": "snowy",
    "cc-possibly-snow-night": "snowy",
    "possibly-thunderstorm-day": "lightning-rainy",
    "cc-possibly-thunderstorm-day": "lightning-rainy",
    "possibly-thunderstorm-night": "lightning-rainy",
    "cc-possibly-thunderstorm-night": "lightning-rainy",
    "rainy": "rainy",
    "cc-rainy": "rainy",
    "sleet": "snowy-rainy",
    "cc-sleet": "snowy-rainy",
    "snow": "snowy",
    "cc-snow": "snowy",
    "thunderstorm": "lightning",
    "cc-thunderstorm": "lightning",
    "cc-windy": "windy"    
    "windy": "windy"
}