"""Example integration using DataUpdateCoordinator."""
from datetime import timedelta
import logging

import async_timeout


from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo

# from homeassistant.helpers.aiohttp_client import async_get_clientsession
# from homeassistant.core import callback
# from homeassistant.exceptions import ConfigEntryAuthFailed,IntegrationError
from homeassistant.helpers.update_coordinator import (
    # CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PORT,
    # CONF_SENSORS,
    CONF_SSL,
    # CONF_VERIFY_SSL,
    CONF_USERNAME,
    CONF_PASSWORD,
)
from .const import CONF_WEBSOCKET

from .moonraker_client import MoonrakerClient, Printer

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=60)


class MoonrakerUpdateCoordinator(DataUpdateCoordinator):
    """My custom coordinator."""

    config_entry: ConfigEntry

    def __init__(
        self, hass: HomeAssistant, config_entry: ConfigEntry, interval: int
    ) -> None:
        """Initialize my coordinator."""
        if config_entry.data.get(CONF_WEBSOCKET) is False:
            super().__init__(
                hass,
                _LOGGER,
                name="Moonraker",
                update_interval=timedelta(seconds=interval),
            )
            _LOGGER.debug("MoonrakerUpdateCoordinator super().__init__ : done")
        else:
            super().__init__(
                hass,
                _LOGGER,
                name="Moonraker",
            )
            _LOGGER.debug(
                "MoonrakerUpdateCoordinator super().__init__ : done (no interval)"
            )

        self._moonraker = MoonrakerClient(
            hass,
            config_entry.data.get(CONF_HOST),
            config_entry.data.get(CONF_NAME),
            config_entry.data.get(CONF_PORT),
            config_entry.data.get(CONF_SSL),
            config_entry.data.get(CONF_WEBSOCKET),
            config_entry.data.get(CONF_USERNAME),
            config_entry.data.get(CONF_PASSWORD),
        )
        self.config_entry = config_entry
        _LOGGER.debug("MoonrakerUpdateCoordinator __init__ : done")

    async def _async_update_data(self):
        """Fetch data from API endpoint."""
        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            async with async_timeout.timeout(10):
                return await self._moonraker.fetch_data()
        except Exception as err:
            _LOGGER.exception(err)
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    async def setup_websocket(self):
        await self._moonraker.websockets_loop(self)

    @property
    def printer(self) -> Printer:
        return self._moonraker.printer

    @property
    def moonraker(self) -> MoonrakerClient:
        return self._moonraker

    @property
    def device_info(self) -> DeviceInfo:
        return self._moonraker.device_info
