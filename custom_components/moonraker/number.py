import logging

from homeassistant.const import (
    PERCENTAGE,
    TEMP_CELSIUS,
    CONF_NAME,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.components.number import NumberEntity


from homeassistant.helpers.typing import StateType

from custom_components.moonraker.common_raker import MoonrakerUpdateCoordinator

from .const import DOMAIN

NUMBERS_LIST = (
    {
        "number_type":"pressure_advance",
        "number_name":"pressure advance",
        "attr_icon": "mdi:printer-3d-nozzle",
        "unit_of_measurement":"s",
        "native_max_value": 1,
        "native_min_value": 0,
        "native_step":0.001,
        "gcode": "SET_PRESSURE_ADVANCE EXTRUDER=extruder ADVANCE={:.3f}",
        "mode":"box",
        },
    {
        "number_type":"max_accel",
        "number_name":"maximun accel",
        "attr_icon": "mdi:printer-3d",
        "unit_of_measurement":"mm/s²",
        "native_max_value": 10000,
        "native_min_value": 0,
        "native_step":100,
        "gcode": "SET_VELOCITY_LIMIT ACCEL={:.0f}",
        "mode":"box",
        },
    {
        "number_type":"max_velocity",
        "number_name":"maximun velocity",
        "attr_icon": "mdi:printer-3d",
        "unit_of_measurement":"mm/s",
        "native_max_value": 10000,
        "native_min_value": 0,
        "native_step":5,
        "gcode": "SET_VELOCITY_LIMIT VELOCITY={:.0f}",
        "mode":"box",
        },
    {
        "number_type":"max_accel_to_decel",
        "number_name":"maximun accel to decel",
        "attr_icon": "mdi:printer-3d",
        "unit_of_measurement":"mm/s²",
        "native_max_value": 10000,
        "native_min_value": 0,
        "native_step":100,
        "gcode": "SET_VELOCITY_LIMIT ACCEL_TO_DECEL={:.0f}",
        "mode":"box",
        },
    {
        "number_type":"square_corner_velocity",
        "number_name":"square corner velocity",
        "attr_icon": "mdi:printer-3d-nozzle",
        "unit_of_measurement":"mm/s",
        "native_max_value": 100,
        "native_min_value": 0,
        "native_step":0.1,
        "gcode": "SET_VELOCITY_LIMIT SQUARE_CORNER_VELOCITY={:.1f}",
        "mode":"box",
        },
    {
        "number_type":"fan_speed",
        "number_name":"Part fan speed",
        "attr_icon": "mdi:fan",
        "unit_of_measurement":PERCENTAGE,
        "native_max_value": 100,
        "native_min_value": 0,
        "native_step":1,
        "gcode": "M106 S{:.0f}", #Convert PCT to 0..255 Range
        "mode":"box",
        },
    )


_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass : HomeAssistant, config_entry : ConfigEntry, async_add_entities : AddEntitiesCallback) -> None :
    """Add numbers for passed config_entry in HA."""
    coordinator: MoonrakerUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    _LOGGER.debug("numbers for entry_id: %s", config_entry.entry_id)
    #device_id = config_entry.unique_id
    device_id=config_entry.data.get(CONF_NAME).lower()
    _LOGGER.debug("numbers for device_id: %s", device_id)
    assert device_id is not None
    
    entities: list[NumberEntity] = []
    for x in NUMBERS_LIST:
        entities.append(MoonrakerNumberBase(
            coordinator,
            x["number_type"],
            device_id,
            x["number_name"],
            x["attr_icon"],
            x["unit_of_measurement"],
            x["native_max_value"],
            x["native_min_value"],
            x["native_step"],
            x["gcode"],
            x["mode"],
            ))

    async_add_entities(entities)


class MoonrakerNumberBase(CoordinatorEntity, NumberEntity):
    should_poll = False

    def __init__(self,
        coordinator : MoonrakerUpdateCoordinator,
        number_type :str,
        device_id: str,
        number_name :str,
        attr_icon:str,
        unit_of_measurement:str,
        native_max_value: float,
        native_min_value: float,
        native_step : float,
        gcode : str,
        mode : str
        ) -> None:

        """Initialize the number."""
        super().__init__(coordinator)
        self._number_type=number_type
        self._number_name=number_name        
        self._device_id=device_id
        self._attr_unique_id = f"{device_id}_{number_type}"
        self._attr_icon = attr_icon
        self._attr_native_unit_of_measurement = unit_of_measurement
        self._attr_native_max_value = native_max_value
        self._attr_native_min_value = native_min_value
        self._attr_native_step = native_step
        self._attr_mode = mode        
        self._gcode = gcode
        _LOGGER.debug("_device_id :%s",self._device_id)
        
    @property
    def name(self) -> str:
        """Return the name of the number."""
        return f"{self._number_type} {self._device_id}"

    @property
    def native_value(self) -> StateType:
        return getattr(self.coordinator.printer,self._number_type)

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        _LOGGER.debug(self._gcode.format(value))
        _LOGGER.debug("NumberEntity :%s",self._number_type)
        try:
            await self.coordinator.moonraker.push_data(self._gcode.format(value))
        except Exception as e:
            _LOGGER.error("async_set_native_value FAILED: %s", self._attr_unique_id)
            raise e 

    @property
    def device_info(self) -> DeviceInfo:
        return self.coordinator.moonraker.device_info
