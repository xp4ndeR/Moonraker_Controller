"""Example integration using DataUpdateCoordinator."""
from typing import Dict, Any
from datetime import timedelta
import logging

import async_timeout

from homeassistant import exceptions
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.core import callback
from homeassistant.exceptions import ConfigEntryAuthFailed,IntegrationError
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .moonraker_client import MoonrakerClient, Printer


_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=30)

class MoonrakerUpdateCoordinator(DataUpdateCoordinator):
    """My custom coordinator."""
    config_entry: ConfigEntry

    def __init__(self, hass : HomeAssistant, moonraker : MoonrakerClient, config_entry : ConfigEntry, interval : int):
        """Initialize my coordinator."""
        super().__init__(hass,_LOGGER, name="Moonraker",update_interval=timedelta(seconds=interval),)
        self._moonraker = moonraker
        self.config_entry = config_entry
        _LOGGER.debug("MoonrakerUpdateCoordinator __init__ : done")

    async def _async_update_data(self):
        """Fetch data from API endpoint.        """
        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            async with async_timeout.timeout(10):
                return await self._moonraker.fetch_data()
        except Exception as err:
            _LOGGER.exception(err)
            raise UpdateFailed(f"Error communicating with API: {err}")

    @property
    def printer(self) -> Printer:
        return self._moonraker._printer

    @property
    def moonraker(self) -> MoonrakerClient:
        return self._moonraker