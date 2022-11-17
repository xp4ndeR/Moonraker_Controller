""" Printer class and attributs parsing """
import logging
import json
from .const import DOMAIN
from homeassistant.helpers.entity import DeviceInfo

_LOGGER = logging.getLogger(__name__)


class Printer:
    """Printer class for Home Assistant"""

    def __init__(self, printerid) -> None:
        self._id = printerid
        self.display_status = DisplayStatus(printerid)
        self.toolhead = Toolhead(printerid)
        self.extruder = Extruder(printerid)
        self.heater_bed = Heater(printerid)
        self.klippy = Klipper(printerid)
        self.fan = Fan(printerid)
        self.webhooks = MoonrakerStats(printerid)
        self._info = None
        self.print_stats = MoonrakerStats(printerid)
        self.mrstats = MoonrakerStats(printerid)
        _LOGGER.debug("Moonraker::Printer created : %s", self._id)

    @property
    def id(self) -> str:
        return self._id

    @property
    def state(self) -> str:
        if hasattr(self.print_stats, "state"):
            return self.print_stats.state
        else:
            return "404"

    @property
    def device_info(self) -> DeviceInfo:
        """Device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._id)},
            manufacturer="Moonraker",
            name="Moonraker",
            #        configuration_url=str(configuration_url),
            sw_version=self.klippy.moonraker_version,
        )

    async def __update(self, component: str, data):
        if hasattr(self, component):
            await getattr(self, component).update(data)

    async def parse(self, data: json):
        """Reading result from query"""
        try:
            if data is not None and "result" in data:
                if "status" in data["result"]:
                    result = data["result"]["status"]
                    for key in result:
                        await self.__update(key, result[key])
                else:
                    _LOGGER.error("Printer.parse : JSON missing status key")
            else:
                _LOGGER.error("Printer.parse : JSON missing result key")
        except Exception as err:
            _LOGGER.error("REQUEST FAILED: %s", err)
            raise err
        # _LOGGER.error("FAILED :D")
        return None

    async def wsparse(self, data: json) -> bool:
        """Reading result from websocket query"""
        _LOGGER.debug("Dataset : %s", json.dumps(data))
        if data is None:
            _LOGGER.warning("Unsuported dataset")
            return False
        if "result" in data:
            await self.parse(data)
        elif "method" in data:
            # match data["method"]:
            #    case "notify_proc_stat_update":
            if data["method"] == "notify_proc_stat_update":
                _LOGGER.info("NFO notify_proc_stat_update")
                for params in data["params"]:
                    self.mrstats.update(params)
            elif data["method"] == "notify_status_update":
                _LOGGER.info("NFO notify_status_update")
                await self.wsupdate(data)
            else:
                _LOGGER.warning("Unsuported method %s", data["method"])
                return False
        return True

    async def wsupdate(self, data):
        """Update specific value"""
        try:
            if data is not None and "params" in data:
                for params in data["params"]:
                    _LOGGER.debug("params %s : %s", type(params), str(params))
                    if isinstance(params, dict):
                        for attr in params:
                            _LOGGER.debug("%s.wsupdate: %s", attr, str(params))
                            self.__update(attr, params[attr])
                    # self._webhooks = result["webhooks"]

        except Exception as err:
            _LOGGER.error("REQUEST FAILED: %s", err)
            raise err
        return None


class PrinterComponent:
    """PrinterComponent class for Home Assistant"""

    def __init__(self, uid) -> None:
        self._id = uid

    async def update(self, data):
        """Update Value from JSON"""
        _LOGGER.debug("%s.update: %s", self.__class__.__name__, str(data))
        if data is not None:
            for attr, value in data.items():
                if hasattr(self, attr):
                    setattr(self, attr, value)
                    _LOGGER.debug(
                        "%s attr: %s :: %s  :: %s",
                        self.__class__.__name__,
                        attr,
                        str(value),
                        getattr(self, attr),
                    )


class Heater(PrinterComponent):
    """HeaterBed class for Home Assistant"""

    def __init__(self, uid) -> None:
        super().__init__(uid)
        self.temperature = None
        self.target = None
        self.power = None

    @property
    def is_on(self) -> bool:
        return True if self.power == 0 else 0


class Extruder(Heater):
    """Extruder class for Home Assistant"""

    def __init__(self, uid) -> None:
        super().__init__(uid)
        self.can_extrude = None
        self.pressure_advance = None
        self.smooth_time = None


class Toolhead(PrinterComponent):
    """Toolhead class for Home Assistant"""

    def __init__(self, uid) -> None:
        super().__init__(uid)
        self.max_accel = None
        self.max_velocity = None
        self.max_accel_to_decel = None
        self.square_corner_velocity = None
        self.homed_axes = None
        self.axis_minimum = None
        self.axis_maximum = None
        self.position = []
        self.extruder = None
        self.stalls = None

    @property
    def position_x(self) -> float:
        if 0 in self.position:
            return self.position[0]
        else:
            return None

    @property
    def position_z(self) -> float:
        if 2 in self.position:
            return self.position[2]
        else:
            return None

    @property
    def position_y(self) -> float:
        if 1 in self.position:
            return self.position[1]
        else:
            return None


class Fan(PrinterComponent):
    """HeaterBed class for Home Assistant"""

    def __init__(self, uid) -> None:
        super().__init__(uid)
        self.speed = None
        self.rpm = None


class DisplayStatus(PrinterComponent):
    """DisplayStatus class for Home Assistant"""

    def __init__(self, uid) -> None:
        super().__init__(uid)
        self.progress = None
        self.message = None


class Klipper(PrinterComponent):
    """Extruder class for Home Assistant"""

    def __init__(self, uid) -> None:
        super().__init__(uid)
        self.klippy_connected = None
        self.klippy_state = None
        self.components = []
        self.failed_components = []
        self.registered_directories = []
        self.warnings = []
        self.websocket_count = 0
        self.moonraker_version = None
        self.missing_klippy_requirements = []
        self.api_version = []
        self.api_version_string = None


class MoonrakerStats:
    """MoonrakerStats class for Home Assistant"""

    def __init__(self, uid) -> None:
        self._id = uid

    async def update(self, data):
        """Update Value from JSON"""
        if data is not None:
            for attr, value in data.items():
                setattr(self, attr, value)
