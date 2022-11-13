"""Moonraker  Number Entity for Home Assistant"""
import logging

from homeassistant.const import (
    PERCENTAGE,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant  # , callback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.components.number import NumberEntity
from .common_raker import MoonrakerUpdateCoordinator
from .const import DOMAIN
from homeassistant.util import slugify as util_slugify

NUMBERS_LIST = (
    {
        "component": "extruder",
        "attribut": "pressure_advance",
        "name": "Pressure advance",
        "attr_icon": "mdi:printer-3d-nozzle",
        "unit_of_measurement": "s",
        "native_max_value": 1,
        "native_min_value": 0,
        "native_step": 0.001,
        "gcode": "SET_PRESSURE_ADVANCE EXTRUDER=extruder ADVANCE={:.3f}",
        "mode": "box",
    },
    {
        "component": "toolhead",
        "attribut": "max_accel",
        "name": "Maximun accel",
        "attr_icon": "mdi:printer-3d",
        "unit_of_measurement": "mm/s²",
        "native_max_value": 10000,
        "native_min_value": 0,
        "native_step": 100,
        "gcode": "SET_VELOCITY_LIMIT ACCEL={:.0f}",
        "mode": "box",
    },
    {
        "component": "toolhead",
        "attribut": "max_velocity",
        "name": "Maximun velocity",
        "attr_icon": "mdi:printer-3d",
        "unit_of_measurement": "mm/s",
        "native_max_value": 10000,
        "native_min_value": 0,
        "native_step": 5,
        "gcode": "SET_VELOCITY_LIMIT VELOCITY={:.0f}",
        "mode": "box",
    },
    {
        "component": "toolhead",
        "attribut": "max_accel_to_decel",
        "name": "maximun accel to decel",
        "attr_icon": "mdi:printer-3d",
        "unit_of_measurement": "mm/s²",
        "native_max_value": 10000,
        "native_min_value": 0,
        "native_step": 100,
        "gcode": "SET_VELOCITY_LIMIT ACCEL_TO_DECEL={:.0f}",
        "mode": "box",
    },
    {
        "component": "toolhead",
        "attribut": "square_corner_velocity",
        "name": "square corner velocity",
        "attr_icon": "mdi:printer-3d-nozzle",
        "unit_of_measurement": "mm/s",
        "native_max_value": 100,
        "native_min_value": 0,
        "native_step": 0.1,
        "gcode": "SET_VELOCITY_LIMIT SQUARE_CORNER_VELOCITY={:.1f}",
        "mode": "box",
    },
    {
        "component": "fan",
        "attribut": "speed",
        "name": "Part fan speed",
        "attr_icon": "mdi:fan",
        "unit_of_measurement": PERCENTAGE,
        "native_max_value": 100,
        "native_min_value": 0,
        "native_step": 1,
        "gcode": "M106 S{:.0f}",  # TODO Convert PCT to 0..255 Range
        "mode": "box",
    },
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add numbers for passed config_entry in HA."""
    coordinator: MoonrakerUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    entities: list[NumberEntity] = []
    for entity in NUMBERS_LIST:
        entities.append(MoonrakerNumberBase(coordinator, entity))

    async_add_entities(entities)


class MoonrakerNumberBase(CoordinatorEntity, NumberEntity):
    """Moonraker Number Enitity for Home Assistant"""

    should_poll = False

    def __init__(
        self, coordinator: MoonrakerUpdateCoordinator, properties: dict
    ) -> None:

        """Initialize the number."""
        super().__init__(coordinator)
        self._attribut = properties["attribut"]
        if "component" in properties:
            self._component = properties["component"]
        self._name = properties["name"]
        self._code = util_slugify(self._name)
        self._device_name = coordinator.moonraker.printer_id
        self._attr_unique_id = f"{self._device_name}_{self._code}"
        self._attr_icon = properties["attr_icon"]
        self._attr_native_unit_of_measurement = properties["unit_of_measurement"]
        self._attr_native_max_value = properties["native_max_value"]
        self._attr_native_min_value = properties["native_min_value"]
        self._attr_native_step = properties["native_step"]
        self._attr_mode = properties["mode"]
        self._gcode = properties["gcode"]

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"{self._name} {self._device_name}"

    @property
    def native_value(self) -> StateType:
        if hasattr(self, "_component") is False:
            return getattr(self.coordinator.printer, self._attribut)
        else:
            return getattr(
                getattr(self.coordinator.printer, self._component), self._attribut
            )

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        try:
            await self.coordinator.moonraker.push_data(self._gcode.format(value))
        except Exception as err:
            _LOGGER.error(
                "FAILED async_set_native_value function for number : %s",
                self._attr_unique_id,
            )
            raise err

    @property
    def device_info(self) -> DeviceInfo:
        return self.coordinator.moonraker.printer.device_info
