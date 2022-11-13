""" Moonraker Climate Base entity """
import logging

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate import (
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, TEMP_CELSIUS
from homeassistant.core import HomeAssistant  # , callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

# from homeassistant.helpers.typing import StateType
from homeassistant.util import slugify as util_slugify
from .common_raker import MoonrakerUpdateCoordinator
from .const import DOMAIN

CLIMATES_LIST = (
    {
        "component": "extruder",
        "climate_type": "temperature",
        "climate_target": "target",
        "climate_power": "power",
        "climate_name": "Extruder",
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
        "component": "heater_bed",
        "climate_type": "temperature",
        "climate_target": "target",
        "climate_power": "power",
        "climate_name": "Heater bed",
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
    """async_setup_entry"""
    coordinator: MoonrakerUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    entities: list[ClimateEntity] = []
    for climate in CLIMATES_LIST:
        entities.append(
            MoonrakerClimateBase(
                coordinator,
                climate["component"],
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
    """Moonraker Climate Base entity"""

    def __init__(
        self,
        coordinator: MoonrakerUpdateCoordinator,
        component: str,
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
        self._device_name = coordinator.moonraker.printer_id
        self._code = util_slugify(self._climate_name)
        self._attr_unique_id = f"{self._device_name}_{self._code}"
        self._attr_icon = attr_icon
        self._attr_temperature_unit = temperature_unit
        self._attr_max_temp = max_temp
        self._attr_min_temp = min_temp
        self._attr_target_temperature_step = target_temperature_step
        self._attr_supported_features = mode
        self._gcode = gcode
        self._attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
        self._component = component
        self._climate_component = getattr(self.coordinator.printer, self._component)

    @property
    def name(self) -> str:
        """Return the name of the number."""
        return f"{self._climate_name} {self._device_name}"

    @property
    def hvac_action(self):
        power = getattr(self._climate_component, self._climate_power)
        trg = getattr(self._climate_component, self._climate_target)
        if trg is None or power is None:
            return HVACAction.OFF
        elif trg > 0 and power > 0:
            return HVACAction.HEATING
        elif trg > 0 and power == 0:
            return HVACAction.IDLE
        else:
            return HVACAction.OFF

    @property
    def current_temperature(self):
        return getattr(self._climate_component, self._climate_type)

    @property
    def target_temperature(self):
        return getattr(self._climate_component, self._climate_target)

    @property
    def hvac_mode(self) -> HVACMode:
        """Set HVAC mode."""
        return (
            HVACMode.HEAT
            if getattr(self._climate_component, self._climate_target) != 0
            else HVACMode.OFF
        )

    @property
    def device_info(self) -> DeviceInfo:
        return self.coordinator.moonraker.printer.device_info

    async def async_set_temperature(self, **kwargs):
        """Send gcode to set target temp"""
        _LOGGER.debug(self._gcode.format(kwargs[ATTR_TEMPERATURE]))
        _LOGGER.debug("ClimateEntity :%s", self._climate_type)
        try:
            await self.coordinator.moonraker.push_data(
                self._gcode.format(kwargs[ATTR_TEMPERATURE])
            )
        except Exception as err:
            _LOGGER.error(
                "FAILED async_set_native_value function: %s", self._attr_unique_id
            )
            raise err
