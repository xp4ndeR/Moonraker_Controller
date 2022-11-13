"""Example integration using DataUpdateCoordinator."""
from datetime import timedelta
import logging
import async_timeout
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo

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
from .const import (
    CONF_WEBSOCKET,
    POLLING,
)  # pylint:disable=unused-import
from .moonraker_client import MoonrakerClient, Printer

_LOGGER = logging.getLogger(__name__)

# SCAN_INTERVAL = timedelta(seconds=POLLING)

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

        self.moonraker = MoonrakerClient(
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

    async def _async_update_data(self):
        """Fetch data from API endpoint."""
        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            async with async_timeout.timeout(10):
                return await self.moonraker.fetch_data()
        except Exception as err:
            _LOGGER.exception(err)
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    async def setup_websocket(self):
        self.hass.async_create_task(self.moonraker.websockets_loop(self))

    @property
    def listeners(self):
        return self._listeners

    @property
    def printer(self) -> Printer:
        return self.moonraker.printer

    @property
    def device_info(self) -> DeviceInfo:
        return self.moonraker.printer.device_info
