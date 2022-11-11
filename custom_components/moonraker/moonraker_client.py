""" Moonraker Client """
# import asyncio
import requests
import functools
import logging
import json
import websockets
from yarl import URL

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.network import get_url

# from homeassistant.helpers import network

from .printer import Printer
from .const import DOMAIN, VERSION  # pylint:disable=unused-import


MR_API = {
    "query": {"http": "/printer/objects/query", "ws": "printer.objects.query"},
}

_LOGGER = logging.getLogger(__name__)


class MoonrakerClient:
    """Moonraker Client class to handle http(s):// or ws:// exchange"""

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
        self._id = name
        self._info = None
        self._protocol = "https" if self._ssl is True else "http"
        _LOGGER.debug("Moonraker::Hub created : %s", self._name)
        self._printer = Printer(self._id)
        self._instance_url = get_url(self._hass)

    @property
    def hub_id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def printer(self) -> Printer:
        return self._printer

    async def server_info(self) -> bool:
        """Test connection"""
        url = URL.build(
            scheme=self._protocol,
            host=self._host,
            port=self._port,
            path="/server/info",
        )
        _LOGGER.debug("test_connection : %s", url)
        headers = {}
        ref_json = {}
        try:
            func = functools.partial(
                requests.get, str(url), headers=headers, json=ref_json
            )
            res = await self._hass.async_add_executor_job(func)
            res.json()
            # self._info=res["result"]
        except Exception as err:
            _LOGGER.error("REQUEST FAILED in test_connection function : %s", err)
            raise err
        _LOGGER.debug("test_connection response code: %s", res.status_code)
        return True if res.status_code == 200 else False

    async def websockets_co(self) -> bool:
        url = URL.build(
            scheme="ws", host=self._host, port=self._port, path="/websocket"
        )

        ref_json = {
            "jsonrpc": "2.0",
            "method": "server.connection.identify",
            "params": {
                "client_name": "home_assistant",
                "version": VERSION,
                "type": "bot",
                "url": self._instance_url,
            },
            "id": 4656,
        }
        try:
            async with websockets.connect(str(url)) as websocket:
                await websocket.send(json.dumps(ref_json))
                res = await websocket.recv()
                _LOGGER.debug("websockets_co response code: %s", res)
                resj= json.loads(res)
                self._connection_id = resj["result"]["connection_id"]
                wslogger = logging.getLogger("websockets")
                wslogger.setLevel(logging.DEBUG)
                wslogger.addHandler(logging.StreamHandler())

        except Exception as err:
            _LOGGER.error("REQUEST FAILED websockets_co : %s", err)
            raise err
        return True if self._connection_id is not None else False

    async def websockets_sub(self):
        url = URL.build(
            scheme="ws", host=self._host, port=self._port, path="/websocket"
        )
        _LOGGER.debug("websockets_co url: %s", url)
        ref_json = {
            "jsonrpc": "2.0",
            "method": "printer.objects.query",
            "params": {
                "client_name": "home_assistant",
                "version": VERSION,
                "type": "bot",
                "url": self._instance_url,
            },
            "id": 4656,
        }
        try:
            async with websockets.connect(str(url)) as websocket:
                await websocket.send(json.dumps(ref_json))
                res = await websocket.recv()
                _LOGGER.debug("websockets response code: %s", res)
        except Exception as err:
            _LOGGER.error("REQUEST FAILED websockets : %s", err)
            raise err
        # return True if res.status_code==200 else False

    async def fetch_data(self):
        url = URL.build(
            scheme=self._protocol,
            host=self._host,
            port=self._port,
            path="/printer/objects/query",
            query_string="display_status&heater_bed&toolhead&extruder&print_stats&webhooks&fan",
        )
        headers = {}
        ref_json = {}
        # await self.websockets_co()
        try:
            func = functools.partial(
                requests.get, str(url), headers=headers, json=ref_json
            )
            res = await self._hass.async_add_executor_job(func)
            await self._printer.parse(res.json())
            # for dev_data in res.json_data or []:
        except Exception as err:
            _LOGGER.error("REQUEST FAILED fetch_data : %s", err)
            raise err
        return True if res.status_code == 200 else False

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
        return True if res.status_code == 200 else False

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
