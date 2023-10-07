"""This module is only used to run some realtime data tests while developing the module.

Create a .env file and add STATION_ID with the id of your station and API_TOKEN with the personal Token.
"""
from __future__ import annotations

from dotenv import load_dotenv
import os
import logging

from pyweatherflow_forecast import (
    WeatherFlow,
    WeatherFlowSensorData,
)

_LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

load_dotenv()
station_id = os.getenv("STATION_ID")
api_token = os.getenv("API_TOKEN")

weatherflow = WeatherFlow(station_id, api_token)

sensor_data: WeatherFlowSensorData = weatherflow.get_sensors()
print("TEMPERATURE:", sensor_data.air_temperature)
print("APPARENT:", sensor_data.feels_like)
print("WIND GUST:", sensor_data.wind_gust)
print("LAST LIGHTNING:", sensor_data.lightning_strike_last_epoch)
print("WIND DIRECTION: ", sensor_data.wind_direction)
print("WIND CARDINAL: ", sensor_data.wind_cardinal)

# data: WeatherFlowStationData = weatherflow.get_station()
# print("STATION NAME: ", data.station_name)

# data: WeatherFlowForecastData = weatherflow.get_forecast()
# print("TEMPERATURE: ", data.temperature)
# print("***** DAILY DATA *****")
# for item in data.forecast_daily:
#     print(item.temperature, item.temp_low, item.icon, item.condition, item.precipitation_probability, item.precipitation, item.wind_bearing, item.wind_speed)
# print("***** HOURLY DATA *****")
# for item in data.forecast_hourly:
#     print(item.datetime, item.temperature, item.apparent_temperature, item.icon, item.condition, item.precipitation, item.precipitation_probability)

