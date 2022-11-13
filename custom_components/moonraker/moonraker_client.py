""" Moonraker Client """
# import asyncio
import requests
from requests import ConnectionError
import functools
import logging
import json
import websockets
from websockets.exceptions import ConnectionClosed  # pylint:disable=unused-import
from yarl import URL

from homeassistant.core import HomeAssistant  # , Callable
from homeassistant.helpers.network import get_url
from homeassistant.util import slugify as util_slugify

# from homeassistant.helpers import network
# from .common_raker import MoonrakerUpdateCoordinator
from .printer import Printer
from .const import DOMAIN, VERSION  # pylint:disable=unused-import

_LOGGER = logging.getLogger(__name__)
wslogger = logging.getLogger("websockets")
wslogger.setLevel(logging.DEBUG)
wslogger.addHandler(logging.StreamHandler())


class MoonrakerClient:
    """Moonraker Client class to handle http(s):// or ws:// exchange"""

    _attr_objects = [
        "display_status",
        "heater_bed",
        "toolhead",
        "extruder",
        "print_stats",
        "webhooks",
        "fan",
        #"heater_fan%20hotend_fan"
    ]

    def __init__(
        self,
        hass: HomeAssistant,
        host: str,
        name: str,
        port: str,
        ssl: bool,
        websocket: bool,
        username: str,
        password: str,
    ) -> None:
        self._connection_id = None
        self._host = host
        self._hass = hass
        self._name = name
        self._port = port
        self._ssl = ssl
        self._websocket = websocket
        self._username = username
        self._password = password
        self._id = util_slugify(self._name)
        self._protocol = "https" if self._ssl is True else "http"
        self._printer = Printer(self._id)
        self._instance_url = get_url(self._hass)
        self._id_number = 0
        self._has_sub = False
        self._last_status_code = None
        self._ws_url = URL.build(
            scheme="ws", host=self._host, port=self._port, path="/websocket"
        )
        self._callbacks = set()

    @property
    def name(self) -> str:
        return self._name

    @property
    def printer_id(self) -> str:
        return self._id

    @property
    def printer(self) -> Printer:
        return self._printer

    # @property
    # def available(self) -> bool:
    #     """Return True if Moonraker is available.  And todo in future if klipper service is running a too."""
    #     return (
    #         True
    #         if self._connection_id is not None or self._last_status_code == 200
    #         else False
    #     )

    async def fetch_data(self):
        #try :
        if self._printer.klippy.klippy_connected is not True :
            await self.server_info()
        return await self.query_objects()


    async def server_info(self) -> bool:
        """Get server information (also used as test connection)"""
        url = URL.build(
            scheme=self._protocol,
            host=self._host,
            port=self._port,
            path="/server/info",
        )
        res = await self._http_get(url)
        if res is not None and "result" in res:
            await self._printer.klippy.update(res["result"])
        return True # TODO HANDLE Connnection failure

    async def query_objects(self):
        """Get Data from HTTP(s) Protocol"""
        url = URL.build(
            scheme=self._protocol,
            host=self._host,
            port=self._port,
            path="/printer/objects/query",
            query_string="&".join(self._attr_objects),
        )
        res = await self._http_get(url)
        await self._printer.parse(res)
        return True # TODO HANDLE Connnection failure

    async def websockets_test(self) -> bool:
        """Get Connection ID using Websocket protocol"""
        try:
            async with websockets.connect(  # pylint:disable=no-member
                str(self._ws_url), ping_interval=None
            ) as websocket:
                await websocket.send(self.ws_json_connect)
                res = await websocket.recv()
                _LOGGER.debug("websockets_co response code: %s", res)
                resj = json.loads(res)
                self._connection_id = resj["result"]["connection_id"]
                _LOGGER.debug("subscribe _connection_id: %s", self._connection_id)
        except Exception as err:
            _LOGGER.error("REQUEST FAILED websockets_co : %s", err)
            raise err
        return True if self._connection_id is not None else False


    async def websockets_loop(self, coordinator):
        """Subscribe to updatefrom websockets Protocol"""
        try:
            async with websockets.connect(  # pylint:disable=no-member
                str(self._ws_url), ping_interval=None
            ) as websocket:
                if self._connection_id is None:
                    await websocket.send(self.ws_json_connect)
                    res = await websocket.recv()
                    resj = json.loads(res)
                    if "result" in resj:
                        self._connection_id = resj["result"]["connection_id"]
                    else:
                        _LOGGER.warning(
                            "Websockets _connection_id not found in : %s", resj
                        )
                    if self._has_sub is False:
                        await websocket.send(self.ws_json_subscribe)
                while coordinator.listeners:
                    res = await websocket.recv()
                    isok = await self._printer.wsparse(json.loads(res))
                    if isok is True:
                        coordinator.async_set_updated_data(isok)
                    _LOGGER.debug("websockets response code: %s", res)
        except ConnectionClosed as err:
            _LOGGER.error("REQUEST websockets : %s", err)
            self._connection_id = None
            self._has_sub = False

    #           continue
    # return True if res.status_code==200 else False



    async def push_data(self, gcode):
        """Send GCODE to moonraker server"""
        url = URL.build(
            scheme=self._protocol,
            host=self._host,
            port=self._port,
            path="/printer/gcode/script",
            # query_string=gcode
        )
        headers = {}
        data = {"script": gcode}
        try:
            func = functools.partial(
                requests.post, str(url), headers=headers, data=data
            )
            res = await self._hass.async_add_executor_job(func)
            _LOGGER.debug("push_data status_code: %s", res.status_code)
        except Exception as err:
            _LOGGER.error("REQUEST FAILED push_data : %s", err)
            raise err
        self._last_status_code = res.status_code
        return True if res.status_code == 200 else False

    @property
    def ws_json_connect(self) -> str:
        return json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "server.connection.identify",
                "params": {
                    "client_name": "home_assistant",
                    "version": VERSION,
                    "type": "bot",
                    "url": self._instance_url,
                },
                "id": self.id_number,
            }
        )

    @property
    def ws_json_subscribe(self) -> str:
        objects = {}
        for param in self._attr_objects:
            objects[param] = None
        return json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "printer.objects.subscribe",
                "params": {"objects": objects},
                "id": self.id_number,
            }
        )

    @property
    def id_number(self):
        self._id_number += 1
        return self._id_number

    async def _http_get(self, url, headers={}, refjson={}) -> json:
        """Get server information using http get"""
        func = functools.partial(
            requests.get, str(url), headers=headers, json=refjson
        )
        result = await self._hass.async_add_executor_job(func)
        if result.status_code!=200:
            raise ConnectionError("REQUEST FAILED for {url} with status code {code}".format(url = str(url),code=result.status_code))
        return result.json()
