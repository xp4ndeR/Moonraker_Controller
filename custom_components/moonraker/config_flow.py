import logging
from typing import Any

import re
import voluptuous as vol

from homeassistant import config_entries, core, exceptions
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant import data_entry_flow
from custom_components.moonraker.moonraker_client import MoonrakerClient

from custom_components.moonraker.const import (
    DOMAIN,
#    PLATFORMS,
    CONF_HOST,
    CONF_NAME,
    CONF_PORT,
    CONF_SSL,
    CONF_USERNAME,
    CONF_PASSWORD,
    DEFAULT_PORT,
    DEFAULT_NAME,
    DEFAULT_HOST
)  # pylint:disable=unused-import



_LOGGER = logging.getLogger(__name__)


DATA_SCHEMA = vol.Schema(
    {
        vol.Required(
            CONF_NAME, default=DEFAULT_NAME, description="Printer Name"
        ): str,
        vol.Required(
            CONF_HOST,  default=DEFAULT_HOST, description="Hostname or IP adresse of moonraker server"
        ): str,
        vol.Required(
            CONF_PORT, default=DEFAULT_PORT, description="Port of your instance of moonraker"
        ): str,        
        vol.Optional(
            CONF_SSL, default=False, description="SSL Enable"
        ): bool,        
        vol.Optional(
            CONF_USERNAME, default="Your username", description="The username used"
        ): str,
        vol.Optional(
            CONF_PASSWORD, default="Your password", description="The password used"): str,
    }
)

async def validate_input(hass: HomeAssistant, data: dict) -> dict[str, Any]:
    if len(data[CONF_HOST]) < 3:
        raise InvalidHost
    hub = MoonrakerClient(hass, data[CONF_HOST], data[CONF_NAME], data[CONF_PORT], data[CONF_SSL], data[CONF_USERNAME],  data[CONF_PASSWORD])
    result = await hub.test_connection()
    if not result:
        raise CannotConnect
    title = hub.hub_id
    _LOGGER.debug("Hub.hub_id: %s", title)
    return {"title": title}

class MoonrakerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)

                return self.async_create_entry(title=info["title"], data=user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidHost:
                errors["host"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        # If there is no user input or there were errors, show the form again, including any errors that were found with the input.
        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )

class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""

class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""

class InvalidHost(exceptions.HomeAssistantError):
    """Error to indicate there is an invalid hostname."""