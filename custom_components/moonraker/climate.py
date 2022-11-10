""" Moonraker Climate Base entity """
import logging

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate import (
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
    #ATTR_FAN_MODE,
    #ATTR_HVAC_MODE,
    #ATTR_PRESET_MODE,
    #ATTR_SWING_MODE,
    #PRESET_NONE,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, CONF_NAME, TEMP_CELSIUS
from homeassistant.core import HomeAssistant #, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
#from homeassistant.helpers.typing import StateType

from .common_raker import MoonrakerUpdateCoordinator
from .const import DOMAIN

CLIMATES_LIST = (
    {
        "climate_type": "extruder_temperature",
        "climate_target": "extruder_temperature_target",
        "climate_power": "extruder_power",
        "climate_name": "extruder",
        "attr_icon": "mdi:printer-3d-nozzle",
        "temperature_unit": TEMP_CELSIUS,
        "max_temp": 300,
        "min_temp": 0,
        "target_temperature_step": 1,
        "gcode": "SET_HEATER_TEMPERATURE HEATER=extruder TARGET={:.0f}",
        "fan_mode": ClimateEntityFeature.FAN_MODE,
        "mode": ClimateEntityFeature.TARGET_TEMPERATURE,
    },
    {
        "climate_type": "heater_bed_temperature",
        "climate_target": "heater_bed_temperature_target",
        "climate_power": "heater_bed_power",
        "climate_name": "heater_bed",
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


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """ async_setup_entry """
    coordinator: MoonrakerUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    device_id = config_entry.data.get(CONF_NAME).lower()
    assert device_id is not None

    entities: list[ClimateEntity] = []
    for climate in CLIMATES_LIST:
        entities.append(
            MoonrakerClimateBase(
                coordinator,
                device_id,
                climate["climate_type"],
                climate["climate_target"],
                climate["climate_power"],
                climate["climate_name"],
                climate["attr_icon"],
                climate["temperature_unit"],
                climate["max_temp"],
                climate["min_temp"],
                climate["target_temperature_step"],
                climate["gcode"],
                climate["mode"],
            )
        )

    async_add_entities(entities)


class MoonrakerClimateBase(CoordinatorEntity, ClimateEntity):
    """ Moonraker Climate Base entity """
    should_poll = False

    def __init__(
        self,
        coordinator: MoonrakerUpdateCoordinator,
        device_id: str,
        climate_type: str,
        climate_target: str,
        climate_power: str,
        climate_name: str,
        attr_icon: str,
        temperature_unit: str,
        max_temp: float,
        min_temp: float,
        target_temperature_step: float,
        gcode: str,
        mode: str,
    ) -> None:

        """Initialize the number."""
        super().__init__(coordinator)
        self._climate_type = climate_type
        self._climate_target = climate_target
        self._climate_power = climate_power
        self._climate_name = climate_name
        self._device_id = device_id
        self._attr_unique_id = f"{device_id}_{climate_type}"
        self._attr_icon = attr_icon
        self._attr_temperature_unit = temperature_unit
        self._attr_max_temp = max_temp
        self._attr_min_temp = min_temp
        self._attr_target_temperature_step = target_temperature_step
        self._attr_supported_features = mode
        self._gcode = gcode
        self._attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
        _LOGGER.debug("_device_id :%s", self._device_id)

    @property
    def name(self) -> str:
        """Return the name of the number."""
        return f"{self._climate_name} {self._device_id}"

    @property
    def hvac_action(self):
        power = getattr(self.coordinator.printer, self._climate_power)
        trg = getattr(self.coordinator.printer, self._climate_target)
        if trg > 0 and power > 0:
            return HVACAction.HEATING
        elif trg > 0 and power == 0:
            return HVACAction.IDLE
        else:
            return HVACAction.OFF

    @property
    def current_temperature(self):
        return getattr(self.coordinator.printer, self._climate_type)

    @property
    def target_temperature(self):
        return getattr(self.coordinator.printer, self._climate_target)

    @property
    def hvac_mode(self) -> HVACMode:
        """Set HVAC mode."""
        return (
            HVACMode.HEAT
            if getattr(self.coordinator.printer, self._climate_target) != 0
            else HVACMode.OFF
        )

    @property
    def device_info(self) -> DeviceInfo:
        return self.coordinator.moonraker.device_info

    async def async_set_temperature(self, **kwargs):
        _LOGGER.debug(self._gcode.format(kwargs[ATTR_TEMPERATURE]))
        _LOGGER.debug("ClimateEntity :%s", self._climate_type)

        try:
            await self.coordinator.moonraker.push_data(
                self._gcode.format(kwargs[ATTR_TEMPERATURE])
            )
        except Exception as err:
            _LOGGER.error("FAILED async_set_native_value function: %s", self._attr_unique_id)
            raise err
