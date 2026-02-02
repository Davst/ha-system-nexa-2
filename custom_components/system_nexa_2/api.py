"""API Client for System Nexa 2."""
import logging
import aiohttp
import asyncio

_LOGGER = logging.getLogger(__name__)

class SystemNexa2Client:
    """Client for controlling System Nexa 2 devices."""

    def __init__(self, host: str, token: str, port: int = 3000) -> None:
        """Initialize the client."""
        self._host = host
        self._port = port
        self._token = token
        self._base_url = f"http://{host}:{port}"
        self._ws_url = f"http://{host}:{port}/live" # Note: aiohttp uses http/https scheme for upgrade
        self._ws: aiohttp.ClientWebSocketResponse | None = None
        self._callback = None
        self._session: aiohttp.ClientSession | None = None

    async def async_get_state(self) -> dict:
        """Get the current state of the device."""
        url = f"{self._base_url}/state"
        headers = {"Content-type": "application/json", "token": self._token}
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers, timeout=10) as response:
                    response.raise_for_status()
                    return await response.json()
            except asyncio.TimeoutError:
                _LOGGER.error("Timeout fetching state from System Nexa 2 device at %s", self._host)
                raise
            except aiohttp.ClientError as err:
                _LOGGER.error("Error fetching state from System Nexa 2 device: %s", err)
                raise

    async def async_set_state(self, value: float) -> dict:
        """Set the state of the device.
        
        Value should be 0 (off), 1 (on), or float 0.0-1.0 (dimmer).
        """
        # We use HTTP primarily for control to ensure we get the immediate response state
        # and to simplify handling of "turn on if off" logic.
        
        url = f"{self._base_url}/state"
        params = {"v": str(value)}
        headers = {"Content-type": "application/json", "token": self._token}

        async with aiohttp.ClientSession() as session:
            try:
                # The API docs show GET for setting state: GET /state?v={value}
                async with session.get(url, params=params, headers=headers, timeout=10) as response:
                    response.raise_for_status()
                    return await response.json()
            except asyncio.TimeoutError:
                _LOGGER.error("Timeout setting state for System Nexa 2 device at %s", self._host)
                raise
            except aiohttp.ClientError as err:
                _LOGGER.error("Error setting state for System Nexa 2 device: %s", err)
                raise

    async def async_set_power(self, state: bool) -> dict:
        """Turn the device on or off.
        
        Args:
           state: True for on, False for off.
        """
        # If toggling on, it might restore last brightness
        params = {"on": "1" if state else "0"}
        
        # We always use HTTP for power toggle to ensure "restore" behavior works as per docs (?on=1)
        # WebSocket behavior for "value": "1" is implied to be full 100%, not restore.
        
        # Fallback to HTTP
        url = f"{self._base_url}/state"
        headers = {"Content-type": "application/json", "token": self._token}

        async with aiohttp.ClientSession() as session:
            try:
                # GET /state?on=1
                async with session.get(url, params=params, headers=headers, timeout=10) as response:
                    response.raise_for_status()
                    return await response.json()
            except asyncio.TimeoutError:
                _LOGGER.error("Timeout setting power for System Nexa 2 device at %s", self._host)
                raise
            except aiohttp.ClientError as err:
                _LOGGER.error("Error setting power for System Nexa 2 device: %s", err)
                raise

    def set_callback(self, callback):
        """Set callback for state updates."""
        self._callback = callback

    async def connect_and_listen(self):
        """Connect to Websocket and listen for updates."""
        self._session = aiohttp.ClientSession()
        
        while True:
            try:
                _LOGGER.debug("Connecting to System Nexa 2 Websocket at %s", self._ws_url)
                async with self._session.ws_connect(self._ws_url) as ws:
                    self._ws = ws
                    
                    # Authenticate/Login (value empty as per docs if no elevated security, but required)
                    # Docs: {"type":"login", "value":""}
                    await ws.send_json({"type": "login", "value": self._token or ""})
                    
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            try:
                                data = msg.json()
                                _LOGGER.debug("Received Websocket message: %s", data)
                                
                                # Docs: {"type":"state", "value":"0.5"}
                                if data.get("type") == "state" and self._callback:
                                    try:
                                        val = float(data.get("value", 0))
                                        self._callback(val)
                                    except ValueError:
                                        pass
                            except ValueError:
                                _LOGGER.error("Received non-JSON Websocket message")
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            _LOGGER.error("Websocket connection error")
                            break
            except Exception as err:
                _LOGGER.error("Websocket error: %s. Reconnecting in 5s...", err)
            
            self._ws = None
            await asyncio.sleep(5) # Reconnect delay

    async def close(self):
        """Close the connection."""
        if self._ws:
            await self._ws.close()
        if self._session:
            await self._session.close()
