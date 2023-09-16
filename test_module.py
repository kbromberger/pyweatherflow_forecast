"""
This module is only used to run some realtime data tests
while developing the module.
Create a .env file and add STATION_ID with the id of your station and API_TOKEN with the personal Token
"""
from __future__ import annotations

from dotenv import load_dotenv
import os
import logging
import json

from pyweatherflow_forecast.wffcst_lib import WeatherFlow, WeatherFlowForecast
from pyweatherflow_forecast.const import ICON_LIST

_LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

load_dotenv()
station_id = os.getenv("STATION_ID")
api_token = os.getenv("API_TOKEN")

weatherflow = WeatherFlow(station_id, api_token)

# key = "possibly-rainy-day"
# value = ICON_LIST.get(key, "exceptional")
# print(value)

data: WeatherFlowForecast = weatherflow.get_forecast()
for item in data:
    print(item.temperature, item.icon)

