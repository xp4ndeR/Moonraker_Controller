""" Printer class and attributs parsing """
import logging

_LOGGER = logging.getLogger(__name__)


class Printer:
    """ Printer class for Home Assistant """
    def __init__(self, printerid) -> None:
        self._id = printerid
        self._progress = None
        self._state = None
        self._toolhead = None
        self._extruder = None
        self._heater_bed = None
        self._fan = None
        self._webhooks = None
        self._print_stats = None
        self._info = None
        _LOGGER.debug("Moonraker::Printer created : %s", self._id)

    @property
    def id(self) -> str:
        return self._id

    @property
    def state(self) -> str:
        return self._state

    @property
    def progress(self) -> str:
        return self._progress

    @property
    def max_accel(self) -> float:
        return self._toolhead["max_accel"]

    @property
    def max_velocity(self) -> float:
        return self._toolhead["max_velocity"]

    @property
    def max_accel_to_decel(self) -> float:
        return self._toolhead["max_accel_to_decel"]

    @property
    def square_corner_velocity(self) -> float:
        return self._toolhead["square_corner_velocity"]

    @property
    def axis_minimum(self) -> list:
        return self._toolhead["homed_axes"]

    @property
    def axis_maximum(self) -> list:
        return self._toolhead["homed_axes"]

    @property
    def position(self) -> list:
        return self._toolhead["position"]

    @property
    def extruder(self) -> str:
        return self._toolhead["extruder"]

    @property
    def pressure_advance(self) -> float:
        return self._extruder["pressure_advance"]

    @property
    def can_extrude(self) -> bool:
        return self._extruder["can_extrude"]

    @property
    def smooth_time(self) -> float:
        return self._extruder["smooth_time"]

    @property
    def extruder_temperature(self) -> float:
        return self._extruder["temperature"]

    @property
    def extruder_temperature_target(self) -> float:
        return self._extruder["target"]

    @property
    def extruder_power(self) -> float:
        return self._extruder["power"] * 100  # verify if necessary for HA

    @property
    def extruder_can_extrude(self) -> bool:
        return self._extruder["can_extrude"]

    @property
    def heater_bed_temperature(self) -> float:
        return self._heater_bed["temperature"]

    @property
    def heater_bed_temperature_target(self) -> float:
        return self._heater_bed["target"]

    @property
    def heater_bed_power(self) -> float:
        return self._heater_bed["power"]

    @property
    def fan_speed(self) -> float:
        return self._fan["speed"]

    @property
    def fan_rpm(self) -> float:
        return self._fan["rpm"]

    @property
    def moonraker_version(self) -> str:
        return "NFO" #self._info["moonraker_version"]

    async def parse(self, data):
        try:
            if data is not None:
                # r = json.loads()
                result = data["result"]["status"]
                _LOGGER.debug("Printer.parse Type %s", type(data["result"]))
                if result is not None:
                    self._progress = result["display_status"]["progress"]
                    self._state = result["print_stats"]["state"]
                    self._heater_bed = result["heater_bed"]
                    self._toolhead = result["toolhead"]
                    self._extruder = result["extruder"]
                    self._webhooks = result["webhooks"]
                    self._print_stats = result["print_stats"]
                    self._fan = result["fan"]
                else:
                    _LOGGER.error("Printer.parse : JSON missing status key")
            else:
                _LOGGER.error("Printer.parse : JSON missing result key")
        except Exception as err:
            _LOGGER.error("REQUEST FAILED: %s", err)
            raise err
        return None
