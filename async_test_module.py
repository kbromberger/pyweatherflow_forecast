"""This module is only used to run some realtime data tests using the async functions, while developing the module.

Create a .env file and add STATION_ID with the id of your station and API_TOKEN with the personal Token.
"""
from __future__ import annotations

from dotenv import load_dotenv
import os
import asyncio
import logging
import time

from pyweatherflow_forecast import (
    WeatherFlow,
    WeatherFlowSensorData,
    WeatherFlowStationData,
)

_LOGGER = logging.getLogger(__name__)

async def main() -> None:
    logging.basicConfig(level=logging.DEBUG)
    start = time.time()

    load_dotenv()
    station_id = os.getenv("STATION_ID")
    api_token = os.getenv("API_TOKEN")
    elevation = 60

    weatherflow = WeatherFlow(station_id=station_id, api_token=api_token, elevation=elevation)
    try:
        station_data: WeatherFlowStationData = await weatherflow.async_get_station()
        print("STATION NAME: ", station_data.station_name)
        print("DEVICE ID: ", station_data.device_id)
        print("FIRMWARE: ", station_data.firmware_revision)
        print("SERIAL: ", station_data.serial_number)

    except Exception as err:
        print(err)

    try:
        sensor_data: WeatherFlowSensorData = await weatherflow.async_get_sensors()
        print("TEMPERATURE:", sensor_data.air_temperature)
        print("APPARENT:", sensor_data.feels_like)
        print("WIND GUST:", sensor_data.wind_gust)
        print("LAST LIGHTNING:", sensor_data.lightning_strike_last_epoch)
        print("WIND DIRECTION: ", sensor_data.wind_direction)
        print("WIND CARDINAL: ", sensor_data.wind_cardinal)
        print("PRECIP CHECKED: ", sensor_data.precip_accum_local_day_final)
        print("ABSOLUTE HUMIDITY: ", sensor_data.absolute_humidity)
        print("VISIBILITY: ", sensor_data.visibility)
        print("BEAUFORT: ", sensor_data.beaufort)
        print("FREEZING ALT: ", sensor_data.freezing_altitude)
        print("VOLTAGE: ", sensor_data.voltage)
        print("BATTERY: ", sensor_data.battery)

    except Exception as err:
        print(err)

    end = time.time()

    _LOGGER.info("Execution time: %s seconds", end - start)

asyncio.run(main())