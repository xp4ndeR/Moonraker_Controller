"""Constants for the moonraker integration."""

NAME = "Moonraker Controller"
DOMAIN = "moonraker"
VERSION = "0.0.1"

ISSUE_URL = "https://github.com/"


CONF_HOST = "host"
CONF_SSL = "ssl"
CONF_PORT = "port"
CONF_NAME = "name"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"

DEFAULT_PORT = "7125"
DEFAULT_NAME = "MyPrinter"
DEFAULT_HOST = "192.168.10.16"


STARTUP_MESSAGE = f"""
-------------------------------------------------------------------

Version: 
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""
