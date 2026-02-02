"""Light platform for System Nexa 2."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.light import (
    LightEntity,
    ColorMode,
    ATTR_BRIGHTNESS,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN
from .api import SystemNexa2Client

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the System Nexa 2 light."""
    client: SystemNexa2Client = hass.data[DOMAIN][entry.entry_id]
    
    # We currently assume one device per host/entry
    async_add_entities([SystemNexa2Light(client, entry)])


class SystemNexa2Light(LightEntity):
    """Representation of a System Nexa 2 Light."""

    _attr_has_entity_name = True
    _attr_name = None  # Use device name
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}
    _attr_color_mode = ColorMode.BRIGHTNESS

    def __init__(self, client: SystemNexa2Client, entry: ConfigEntry) -> None:
        """Initialize the light."""
        self._client = client
        self._entry = entry
        self._attr_unique_id = entry.entry_id
        
        # Use existing unique_id (from mDNS) to identify device if possible
        # This fixes duplicate devices in registry if re-added
        identifiers = {(DOMAIN, entry.entry_id)}
        if entry.unique_id:
            identifiers.add((DOMAIN, entry.unique_id))
            
        self._attr_device_info = DeviceInfo(
            identifiers=identifiers,
            name=entry.title,
            manufacturer="Nexa",
            model="System Nexa 2",
        )
        self._state_value = 0.0

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        self._client.set_callback(self._handle_update)
        self._entry.async_create_background_task(
            self.hass, self._client.connect_and_listen(), "system_nexa_2_ws"
        )
        # Initial fetch
        await self.async_update()

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity will be removed from hass."""
        await self._client.close()

    def _handle_update(self, value: float) -> None:
        """Handle incoming state update from websocket."""
        self._state_value = value
        self._attr_is_on = value > 0
        if value > 0:
            self._attr_brightness = int(value * 255)
        else:
            self._attr_brightness = 0
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        
        if brightness is not None:
             # Scale 0-255 to 0.0-1.0
             value = brightness / 255.0
             try:
                await self._client.async_set_state(value)
                # The API often returns stale state (e.g. 0.00) immediately after setting a value.
                # We optimistically update to the requested value since the user confirmed `v` controls power.
                self._handle_update(value)
             except Exception as err:
                _LOGGER.error("Failed to set brightness: %s", err)
        else:
             # No brightness -> Use power on (restore)
             try:
                 res = await self._client.async_set_power(True)
                 # For toggle ON, we must rely on response because we don't know the restored level
                 if "state" in res:
                      self._handle_update(float(res["state"]))
             except Exception as err:
                 _LOGGER.error("Failed to turn on light: %s", err)
             # No brightness -> Use power on (restore)
             try:
                 res = await self._client.async_set_power(True)
                 if "state" in res:
                      self._handle_update(float(res["state"]))
             except Exception as err:
                 _LOGGER.error("Failed to turn on light: %s", err)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        try:
            await self._client.async_set_power(False)
            self._handle_update(0.0)
        except Exception as err:
            _LOGGER.error("Failed to turn off light: %s", err)

    async def async_update(self) -> None:
        """Fetch new state data for this light."""
        try:
            data = await self._client.async_get_state()
            # data received: {'state': 0.5}
            val = float(data.get('state', 0))
            self._handle_update(val)
                
        except Exception as err:
            _LOGGER.error("Failed to update light: %s", err)
