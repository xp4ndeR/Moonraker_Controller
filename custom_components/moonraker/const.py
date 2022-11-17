"""Constants for the moonraker integration."""
from homeassistant.components.climate import (
    ClimateEntityFeature,
)

from homeassistant.const import TEMP_CELSIUS

NAME = "Moonraker Controller"
DOMAIN = "moonraker"
VERSION = "0.0.2"

ISSUE_URL = "https://github.com/xp4ndeR/Moonraker_Controller/issues"


CONF_WEBSOCKET = "websocket"
CONF_PRINTER_OBJECTS = "printer_objects"
DEFAULT_PRINTER_OBJECTS = [
    "display_status",
    "heater_bed",
    "toolhead",
    "print_stats",
    "webhooks",
    "fan",
]
CONF_PRINTER_EXTRUDERS = "extruder"
DEFAULT_PRINTER_EXTRUDERS = "extruder"

CONF_PRINTER_HEATER_FAN = "heater_fan"
DEFAULT_PRINTER_HEATER_FAN = "hotend_fan"

CONF_PRINTER_FILAMENT_SWITCH_SENSOR = "filament_switch_sensor"
DEFAULT_PRINTER_FILAMENT_SWITCH_SENSOR = None

DEFAULT_PORT = "7125"
DEFAULT_NAME = "MyPrinter"
DEFAULT_HOST = "192.168.10.16"
POLLING = 60
PERCENTAGE = "%"
DISTANCE = "mm"

SENSORS_LIST = (
    {
        "attribut": "klippy_state",
        "component": "klippy",
        "name": "Klipper State",
        "attr_icon": "mdi:heating-coil",
        "unit_of_measurement": None,
    },
    {
        "attribut": "klippy_connected",
        "component": "klippy",
        "name": "Klipper Connected",
        "attr_icon": "mdi:heating-coil",
        "unit_of_measurement": None,
    },
    {
        "attribut": "power",
        "component": "heater_bed",
        "name": "extruder_power",
        "attr_icon": "mdi:printer-3d",
        "unit_of_measurement": PERCENTAGE,
    },
    {
        "component": "display_status",
        "attribut": "progress",
        "name": "Progress",
        "attr_icon": "mdi:printer-3d",
        "unit_of_measurement": PERCENTAGE,
    },
    {
        "component": "print_stats",
        "attribut": "state",
        "name": "State",
        "attr_icon": "mdi:printer-3d",
        "unit_of_measurement": None,
    },
    {
        "component": "toolhead",
        "attribut": "position_x",
        "name": "Position X",
        "attr_icon": "mdi:printer-3d",
        "unit_of_measurement": DISTANCE,
    },
    {
        "component": "toolhead",
        "attribut": "position_z",
        "name": "Position Z",
        "attr_icon": "mdi:printer-3d",
        "unit_of_measurement": DISTANCE,
    },
    {
        "component": "toolhead",
        "attribut": "position_y",
        "name": "Position Y",
        "attr_icon": "mdi:printer-3d",
        "unit_of_measurement": DISTANCE,
    },
    {
        "component": "toolhead",
        "attribut": "extruder",
        "name": "Active extruder",
        "attr_icon": "mdi:printer-3d",
        "unit_of_measurement": None,
    },
    {
        "component": "extruder",
        "attribut": "can_extrude",
        "name": "Extruder can extrude",
        "attr_icon": "mdi:printer-3d",
        "unit_of_measurement": None,
    },
)


CLIMATES_LIST = (
    {
        "component": "heater_bed",
        "climate_type": "temperature",
        "climate_target": "target",
        "climate_power": "power",
        "name": "Heater bed",
        "attr_icon": "mdi:heating-coil",
        "temperature_unit": TEMP_CELSIUS,
        "max_temp": 120,
        "min_temp": 0,
        "target_temperature_step": 5,
        "gcode": "SET_HEATER_TEMPERATURE HEATER=heater_bed TARGET={:.0f}",
        "fan_mode": ClimateEntityFeature.FAN_MODE,
        "mode": ClimateEntityFeature.TARGET_TEMPERATURE,
    },
)

STARTUP_MESSAGE = f"""
-------------------------------------------------------------------

Version: {VERSION}
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""
