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



    end = time.time()

    _LOGGER.info("Execution time: %s seconds", end - start)

asyncio.run(main())