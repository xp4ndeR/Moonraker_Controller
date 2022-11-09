import asyncio
import random
import requests
import functools
import logging
import json
import websockets
from yarl import URL

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from custom_components.moonraker.const import (
    DOMAIN,
#    PLATFORMS,
    CONF_HOST,
    CONF_PORT,
    CONF_NAME,
    CONF_SSL,
    CONF_USERNAME,
    CONF_PASSWORD,
    VERSION
)  # pylint:disable=unused-import


MR_API = {
    "query" : {"http": "/printer/objects/query", "ws" :"printer.objects.query"},
}

_LOGGER = logging.getLogger(__name__)

class MoonrakerClient:

    def __init__(self, hass: HomeAssistant, host: str, name: str, port: str, ssl: str, username: str, password: str) -> None:
        self._connection_id = None
        self._host = host
        self._hass = hass
        self._name = name
        self._port = port
        self._ssl = ssl
        self._username = username
        self._password = password
        self._id = name
        self._info = None
        self._protocol = "https" if self._ssl==True else "http"
        _LOGGER.debug("Moonraker::Hub created : %s",  self._name)
        self._printer= Printer(self._id)
        

    @property
    def hub_id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    #@property
    #def printer(self) -> Printer:
    #    return self._printer

    async def test_connection(self) -> bool:
        url =URL.build(
            scheme=self._protocol,
            host=self._host,
            port=self._port,
            path="/server/info",
        )
        _LOGGER.debug("test_connection : %s", url)
        headers = {}
        ref_json = {} 
        try:
            func = functools.partial(requests.get, str(url), headers=headers, json=ref_json)
            res = await self._hass.async_add_executor_job(func)
            res.json()
            #self._info=res["result"]
        except Exception as e:
            _LOGGER.error("test_connection REQUEST FAILED: %s", e)
            raise e
        _LOGGER.debug("test_connection response code: %s", res.status_code)
        return True if res.status_code==200 else False

    async def websockets_co(self):
        url =URL.build(
            scheme="ws",
            host=self._host,
            port=self._port,
            path="/websocket"
        )
        _LOGGER.debug("websockets_co url: %s", url)
        headers = {}
        ref_json = {"jsonrpc": "2.0", "method": "server.connection.identify", "params": { "client_name": "home_assistant",
        "version": VERSION, "type": "bot", "url": "http://homeassistant.local:8123"}, "id": 4656}           
        try:
            async with websockets.connect(str(url)) as websocket:
                    await websocket.send(json.dumps(ref_json))
                    res= await websocket.recv()
                    wslogger = logging.getLogger('websockets')
                    wslogger.setLevel(logging.DEBUG)
                    wslogger.addHandler(logging.StreamHandler())
                    _LOGGER.debug("websockets_co response code: %s", res)
        except Exception as e:
            _LOGGER.error("websockets_co REQUEST FAILED: %s", e)
            raise e
        #return True if res.status_code==200 else False

    async def websockets(self):
        url =URL.build(
            scheme="ws",
            host=self._host,
            port=self._port,
            path="/websocket"
        )
        _LOGGER.debug("websockets_co url: %s", url)
        headers = {}
        ref_json = {"jsonrpc": "2.0", "method": "printer.objects.query", "params": { "client_name": "home_assistant",
        "version": VERSION, "type": "bot", "url": "http://homeassistant.local:8123"}, "id": 4656}           
        try:
            async with websockets.connect(str(url)) as websocket:
                    await websocket.send(json.dumps(ref_json))
                    res= await websocket.recv()
                    _LOGGER.debug("websockets_co response code: %s", res)
        except Exception as e:
            _LOGGER.error("websockets_co REQUEST FAILED: %s", e)
            raise e
        #return True if res.status_code==200 else False


    async def fetch_data(self):
        url =URL.build(
            scheme=self._protocol,
            host=self._host,
            port=self._port,
            path="/printer/objects/query",
            query_string="display_status&heater_bed&toolhead&extruder&print_stats&webhooks&fan"
        )
        headers = {}
        ref_json = {}
        #await self.websockets_co()
        try:
            func = functools.partial(requests.get, str(url), headers=headers, json=ref_json)
            res = await self._hass.async_add_executor_job(func)
            await self._printer.parse(res.json())
            #for dev_data in res.json_data or []:
        except Exception as e:
            _LOGGER.error("fetch_data REQUEST FAILED: %s", e)
            raise e    
        return True if res.status_code==200 else False

    async def push_data(self,gcode):
        url =URL.build(
            scheme=self._protocol,
            host=self._host,
            port=self._port,
            path="/printer/gcode/script",
            #query_string=gcode
        )
        headers = {}
        data = {"script":gcode}
        try:
            func = functools.partial(requests.post, str(url), headers=headers, data=data)
            res = await self._hass.async_add_executor_job(func)
            _LOGGER.debug("push_data status_code: %s", res.status_code)
        except Exception as e:
            _LOGGER.error("push_data REQUEST FAILED: %s", e)
            raise e    
        return True if res.status_code==200 else False



    @property
    def device_info(self) -> DeviceInfo:
        """Device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._id)},
            manufacturer="Moonraker",
            name="Moonraker",
    #        configuration_url=str(configuration_url),
    #        sw_version=self._printer.moonraker_version,
            )

class Printer:

    def __init__(self,id) -> None:
        self._id =id
        self._progress = None
        self._state = None
        self._toolhead = None
        self._extruder = None
        self._heater_bed = None
        self._fan = None
        self._webhooks = None
        self._print_stats = None
        _LOGGER.debug("Moonraker::Printer created : %s",  self._id)

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
        return self._extruder["power"]*100 #verify if necessary for HA

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
        return self._info["moonraker_version"]

    async def parse(self,data):
        try:
            if data is not None :
                #r = json.loads()
                result=data["result"]["status"]
                _LOGGER.debug("Printer.parse Type %s",type(data["result"]))
                if result is not None :
                    self._progress=result["display_status"]["progress"]
                    self._state=result["print_stats"]["state"]
                    self._heater_bed=result["heater_bed"]
                    self._toolhead=result["toolhead"]
                    self._extruder=result["extruder"]
                    self._webhooks=result["webhooks"]
                    self._print_stats=result["print_stats"]                    
                    self._fan=result["fan"]
                else:
                    _LOGGER.error("Printer.parse : JSON missing status key")
            else:
                _LOGGER.error("Printer.parse : JSON missing result key")
        except Exception as e:
            _LOGGER.error("REQUEST FAILED: %s", e)
            raise e    
        return None
