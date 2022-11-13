""" Printer class and attributs parsing """
import logging
import json

_LOGGER = logging.getLogger(__name__)


class Printer:
    """Printer class for Home Assistant"""

    def __init__(self, printerid) -> None:
        self._id = printerid
        self.display_status = DisplayStatus(printerid)
        self.toolhead = Toolhead(printerid)
        self.extruder = Extruder(printerid)
        self.heater_bed = Heater(printerid)
        self.fan = Fan(printerid)
        self._state = None
        self._webhooks = None
        self._print_stats = None
        self._info = None
        self.mrstats = MoonrakerStats(printerid)
        _LOGGER.debug("Moonraker::Printer created : %s", self._id)

    @property
    def id(self) -> str:
        return self._id

    @property
    def state(self) -> str:
        return self._state

    @property
    def moonraker_version(self) -> str:
        return "NFO"  # self._info["moonraker_version"]

    async def parse(self, data):
        """Reading result from query"""
        try:
            if data is not None and "result" in data:
                if "status" in data["result"]:
                    result = data["result"]["status"]
                    self._state = result["print_stats"]["state"]
                    if "heater_bed" in result:
                        await self.heater_bed.update(result["heater_bed"])
                    if "extruder" in result:
                        await self.extruder.update(result["extruder"])
                    if "toolhead" in result:
                        await self.toolhead.update(result["toolhead"])
                    if "fan" in result:
                        await self.fan.update(result["fan"])
                    if "display_status" in result:
                        await self.display_status.update(result["display_status"])

                    self._webhooks = result["webhooks"]
                    self._print_stats = result["print_stats"]
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
                            if attr == "heater_bed":
                                await self.heater_bed.update(params[attr])
                            elif attr == "extruder":
                                await self.extruder.update(params[attr])
                            elif attr == "toolhead":
                                await self.toolhead.update(params[attr])
                            elif attr == "fan":
                                await self.fan.update(params[attr])
                            elif attr == "display_status":
                                await self.display_status.update(params[attr])

                    # self._state = result["print_stats"]["state"]
                    # self._webhooks = result["webhooks"]
                    # self._print_stats = result["print_stats"]

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


class MoonrakerStats:
    """MoonrakerStats class for Home Assistant"""

    def __init__(self, uid) -> None:
        self._id = uid

    async def update(self, data):
        """Update Value from JSON"""
        if data is not None:
            for attr, value in data.items():
                setattr(self, attr, value)
