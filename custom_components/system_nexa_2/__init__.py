"""The System Nexa 2 integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, CONF_HOST, CONF_TOKEN
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .api import SystemNexa2Client

PLATFORMS: list[Platform] = [Platform.LIGHT]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up System Nexa 2 from a config entry."""
    
    hass.data.setdefault(DOMAIN, {})
    
    client = SystemNexa2Client(entry.data[CONF_HOST], entry.data[CONF_TOKEN])
    
    # Store the client in hass.data so platforms can access it
    hass.data[DOMAIN][entry.entry_id] = client

    # Verify connection one more time? Usually not needed if config flow checked it, 
    # but good for startup logs.
    # For now we skip it to speed up startup.

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
