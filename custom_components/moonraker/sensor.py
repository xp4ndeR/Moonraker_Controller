import logging

from homeassistant.const import (
    PERCENTAGE,
    #    TEMP_CELSIUS,
    CONF_NAME,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant #, callback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo

from homeassistant.components.sensor import (
    #SensorDeviceClass,
    SensorEntity,
    #SensorStateClass,
)

from .common_raker import MoonrakerUpdateCoordinator

from .const import DOMAIN

SENSORS_LIST = (
    {
        "sensor_type": "heater_bed_power",
        "sensor_name": "header bed power",
        "attr_icon": "mdi:heating-coil",
        "unit_of_measurement": None,
    },
    {
        "sensor_type": "extruder_power",
        "sensor_name": "extruder_power",
        "attr_icon": "mdi:printer-3d",
        "unit_of_measurement": PERCENTAGE,
    },
    {
        "sensor_type": "progress",
        "sensor_name": "Progress",
        "attr_icon": "mdi:printer-3d",
        "unit_of_measurement": PERCENTAGE,
    },
    {
        "sensor_type": "state",
        "sensor_name": "State",
        "attr_icon": "mdi:printer-3d",
        "unit_of_measurement": None,
    },
)

#    _attr_native_unit_of_measurement = TEMP_CELSIUS
#    _attr_device_class = SensorDeviceClass.TEMPERATURE
#    _attr_state_class = SensorStateClass.MEASUREMENT

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add sensors for passed config_entry in HA."""
    coordinator: MoonrakerUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    _LOGGER.debug("Sensors for entry_id: %s", config_entry.entry_id)
    # device_id = config_entry.unique_id
    device_id = config_entry.data.get(CONF_NAME).lower()
    _LOGGER.debug("Sensors for device_id: %s", device_id)
    assert device_id is not None

    entities: list[SensorEntity] = []
    for x in SENSORS_LIST:
        entities.append(
            MoonrakerSensorBase(
                coordinator,
                x["sensor_type"],
                device_id,
                x["sensor_name"],
                x["attr_icon"],
                x["unit_of_measurement"],
            )
        )

    async_add_entities(entities)


class MoonrakerSensorBase(CoordinatorEntity, SensorEntity):
    """ Moonraker Sensor Base entity for Home Assistant """
    should_poll = False

    def __init__(
        self,
        coordinator: MoonrakerUpdateCoordinator,
        sensor_type: str,
        device_id: str,
        sensor_name: str,
        attr_icon: str,
        unit_of_measurement: str,
    ) -> None:

        """Initialize the sensor."""
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._sensor_name = sensor_name
        self._device_id = device_id
        self._attr_unique_id = f"{device_id}_{sensor_type}"
        self._attr_icon = attr_icon
        self._attr_native_unit_of_measurement = unit_of_measurement

        _LOGGER.debug("_device_id :%s", self._device_id)

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return f"{self._device_id} {self._sensor_type}"

    @property
    def native_value(self) -> StateType:
        return getattr(self.coordinator.printer, self._sensor_type)

    @property
    def device_info(self) -> DeviceInfo:
        return self.coordinator.device_info
