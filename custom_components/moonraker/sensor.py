""" MoonrakerSensorBase """
import logging

from homeassistant.const import (
    PERCENTAGE,
    #    TEMP_CELSIUS,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.components.sensor import (
    # SensorDeviceClass,
    SensorEntity,
    # SensorStateClass,
)
from homeassistant.util import slugify as util_slugify
from .common_raker import MoonrakerUpdateCoordinator
from .const import DOMAIN

SENSORS_LIST = (
    {
        "attribut": "power",
        "component": "heater_bed",
        "name": "header bed power",
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
        "unit_of_measurement": "mm",
    },
    {
        "component": "toolhead",
        "attribut": "position_z",
        "name": "Position Z",
        "attr_icon": "mdi:printer-3d",
        "unit_of_measurement": "mm",
    },
    {
        "component": "toolhead",
        "attribut": "position_y",
        "name": "Position Z",
        "attr_icon": "mdi:printer-3d",
        "unit_of_measurement": "mm",
    },
    {
        "component": "extruder",
        "attribut": "can_extrude",
        "name": "Extruder can extrude",
        "attr_icon": "mdi:printer-3d",
        "unit_of_measurement": None,
    },
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add sensors for passed config_entry in HA."""
    coordinator: MoonrakerUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    entities: list[SensorEntity] = []
    for param in SENSORS_LIST:
        entities.append(MoonrakerSensorBase(coordinator, param))

    async_add_entities(entities)


class MoonrakerSensorBase(CoordinatorEntity, SensorEntity):
    """Moonraker Sensor Base entity for Home Assistant"""

    should_poll = False

    def __init__(
        self, coordinator: MoonrakerUpdateCoordinator, properties: dict
    ) -> None:
        """Initialize the sensor."""
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

    @property
    def device_info(self) -> DeviceInfo:
        return self.coordinator.moonraker.printer.device_info
