"""Moonraker Controller."""
from __future__ import annotations

from datetime import timedelta
import logging
import asyncio
from typing import cast
import voluptuous as vol
import homeassistant.util.dt as dt_util

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.typing import ConfigType

from homeassistant.const import (
    #    CONF_API_KEY,
    #    CONF_BINARY_SENSORS,
    CONF_HOST,
    # CONF_MONITORED_CONDITIONS,
    CONF_NAME,
    # CONF_PATH,
    CONF_PORT,
    # CONF_SENSORS,
    CONF_SSL,
    # CONF_VERIFY_SSL,
    CONF_USERNAME,
    CONF_PASSWORD,
    Platform,
)

from .const import (
    DOMAIN,
    CONF_WEBSOCKET,
    DEFAULT_PORT,
    DEFAULT_NAME,
    DEFAULT_HOST,
    VERSION,
    POLLING,
)  # pylint:disable=unused-import


from .common_raker import MoonrakerUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.CLIMATE, Platform.SENSOR, Platform.NUMBER]


@asyncio.coroutine
def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Do async_setup stuff"""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Setup Moonraker Controller from a config entry."""
    try:
        coordinator = MoonrakerUpdateCoordinator(hass, entry, POLLING)
        await coordinator.async_config_entry_first_refresh()

        hass.data[DOMAIN][entry.entry_id] = coordinator
        for component in PLATFORMS:
            hass.async_create_task(
                hass.config_entries.async_forward_entry_setup(entry, component)
            )
        return True
    except Exception as err:
        _LOGGER.exception(err)
        raise ConfigEntryNotReady from err


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Delete Moonraker Controller from a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
