"""Constants for the moonraker integration."""

NAME = "Moonraker Controller"
DOMAIN = "moonraker"
VERSION = "0.0.2"

ISSUE_URL = "https://github.com/xp4ndeR/Moonraker_Controller/issues"


CONF_WEBSOCKET = "websocket"

DEFAULT_PORT = "7125"
DEFAULT_NAME = "MyPrinter"
DEFAULT_HOST = "192.168.10.16"
POLLING = 30

STARTUP_MESSAGE = f"""
-------------------------------------------------------------------

Version: {VERSION}
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""
