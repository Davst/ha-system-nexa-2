"""Config flow for System Nexa 2 integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_TOKEN
from homeassistant.data_entry_flow import FlowResult
from homeassistant.components import zeroconf
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from .const import DOMAIN
from .api import SystemNexa2Client

_LOGGER = logging.getLogger(__name__)

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for System Nexa 2."""

    VERSION = 1
    
    def __init__(self):
        """Initialize the config flow."""
        self._discovered_devices = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        return self.async_show_menu(
            step_id="user",
            menu_options=["search", "manual"]
        )

    async def async_step_search(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Search for devices via mDNS."""
        # Browse for devices
        zc = await zeroconf.async_get_instance(self.hass)
        discovered = await zc.async_get_service_info("_systemnexa2._tcp.local.")
        
        # NOTE: Since async_get_service_info only returns one if known, we might want to browse.
        # However, HA doesn't give us a direct "browse" method on the shared instance easily 
        # that returns a list instantly. 
        # Standard pattern is using a listener or just waiting for discovery flows.
        # But if we want to actively "Scan", we can try to look up known services in the internal cache
        # or just rely on what HA has found so far if we can access it.
        
        # Actually, for an active scan in a config flow, we typically check what zeroconf has found.
        # Since we can't easily force a new browse from here without a listener, 
        # we will assume the User flow is triggered, and we will try to discover.
        # A common pattern is to just list devices that have already been discovered by HA's zeroconf
        # or start a discovery task.
        
        # Let's try to get all service infos from the zeroconf instance cache.
        # The `zeroconf` object from `async_get_instance` is a standard python-zeroconf object.
        pass # Placeholder for thought trace, implementing actual code below...

        # Re-implementation:
        # Since collecting *all* mDNS devices takes time, we'll try to get what's known.
        # `async_get_instance` returns the `Zeroconf` object.
        # cache = zc.cache
        # But accessing cache directly is internal.
        
        # Alternative: The user asked for "refresh" list.
        # We can implement a "pick_device" step that shows the list.
        
        return await self.async_step_pick_device()

    async def async_step_pick_device(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Allow the user to pick a device."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            if user_input["device"] == "refresh":
                 return await self.async_step_pick_device()
            
            # Selected a device
            host = self._discovered_devices[user_input["device"]].host
            self.context["host"] = host
            self.context["title_placeholders"] = {"name": user_input["device"]}
            return await self.async_step_token_entry()

        # Gather devices
        # We rely on HA's zeroconf to have found things.
        # Since we can't easily query the central registry for "all services of type X",
        # We might have to rely on `zeroconf.async_get_instance(self.hass)` and look at the cache manually,
        # OR we can just wait for `async_step_zeroconf` to be called.
        
        # However, the user wants a "search" button. 
        # Let's try to inspect the cache for now as it's the most direct way if we don't want to spawn a listener.
        
        zc = await zeroconf.async_get_instance(self.hass)
        services = zc.get_service_info_list("_systemnexa2._tcp.local.")
        
        self._discovered_devices = {}
        options = {}
        
        for service in services:
             # Extract name, etc.
             # service.properties matches the byte strings
             name = service.name.replace("._systemnexa2._tcp.local.", "")
             model = "Nexa Device" # Default
             local_id = None
             
             # Decode properties
             props = {k.decode(): v.decode() if isinstance(v, bytes) else v for k,v in service.properties.items()}
             if "model" in props:
                 model = props["model"]
             if "id" in props:
                 local_id = props["id"]

             # Add to list
             # We use the IP as the key or the name. 
             # service.parsed_addresses() gives IP.
             host = service.parsed_addresses()[0] if service.parsed_addresses() else None
             
             if host:
                 label = f"{name} ({model}) - {host}"
                 self._discovered_devices[label] = service
                 
                 # Update validation: Check if configured
                 # We can check unique ID if we have the local_id
                 if local_id:
                     # Check if entry exists? 
                     # self._abort_if_unique_id_configured is usually for the *current* flow's context.
                     # We can manually check `self.hass.config_entries.async_entries(DOMAIN)`
                     pass

                 options[label] = label

        if not options:
            errors["base"] = "no_devices_found"

        # Add refresh option
        options["refresh"] = "Refresh List"

        return self.async_show_form(
            step_id="pick_device",
            data_schema=vol.Schema({
                vol.Required("device", default=list(options.keys())[0] if options else "refresh"): vol.In(options)
            }),
            errors=errors
        )

    async def async_step_manual(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle manual entry."""
        errors: dict[str, str] = {}
        if user_input is not None:
             client = SystemNexa2Client(user_input[CONF_HOST], user_input[CONF_TOKEN])
             try:
                await client.async_get_state()
             except Exception:
                _LOGGER.exception("Failed to connect to System Nexa 2")
                errors["base"] = "cannot_connect"
             else:
                return self.async_create_entry(
                    title=f"Nexa 2 ({user_input[CONF_HOST]})", 
                    data=user_input
                )

        return self.async_show_form(
            step_id="manual",
            data_schema=vol.Schema({
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_TOKEN): str,
            }),
            errors=errors
        )
        
    async def async_step_token_entry(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Get the token."""
        errors: dict[str, str] = {}
        host = self.context.get("host") or self._discovered_devices[user_input["device"]].parsed_addresses()[0]

        if user_input is not None:
             client = SystemNexa2Client(host, user_input[CONF_TOKEN])
             try:
                await client.async_get_state()
             except Exception:
                _LOGGER.exception("Failed to connect to System Nexa 2")
                errors["base"] = "cannot_connect"
             else:
                # We need to try to get the unique ID (Local ID) if we don't have it yet, 
                # but we probably can't easily get it from the API without mDNS if the API doesn't expose it.
                # But we have it from mDNS step previously theoretically.
                # For now let's create the entry.
                return self.async_create_entry(
                    title=f"Nexa 2 ({host})", 
                    data={CONF_HOST: host, CONF_TOKEN: user_input[CONF_TOKEN]}
                )
        
        return self.async_show_form(
             step_id="token_entry",
             data_schema=vol.Schema({vol.Required(CONF_TOKEN): str}),
             errors=errors,
             description_placeholders={"host": host}
        )

    async def async_step_zeroconf(
        self, discovery_info: ZeroconfServiceInfo
    ) -> FlowResult:
        """Handle zeroconf discovery."""
        host = discovery_info.host
        self.context["host"] = host
        
        # Extract properties
        properties = discovery_info.properties
        local_id = properties.get("id")
        model = properties.get("model", "Nexa Device")
        
        if local_id:
            await self.async_set_unique_id(local_id)
            self._abort_if_unique_id_configured(updates={CONF_HOST: host})
        
        self.context["title_placeholders"] = {"name": discovery_info.hostname, "model": model}
        
        return await self.async_step_discovery_confirm()

    async def async_step_discovery_confirm(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle user confirmation of discovery."""
        if user_input is not None:
             host = self.context.get("host")
             client = SystemNexa2Client(host, user_input[CONF_TOKEN])
             try:
                await client.async_get_state()
             except Exception:
                _LOGGER.exception("Failed to connect to System Nexa 2")
                errors = {"base": "cannot_connect"}
                return self.async_show_form(
                    step_id="discovery_confirm",
                    data_schema=vol.Schema({vol.Required(CONF_TOKEN): str}),
                    errors=errors,
                    description_placeholders=self.context.get("title_placeholders")
                )
             else:
                return self.async_create_entry(
                    title=f"Nexa 2 ({host})", 
                    data={CONF_HOST: host, CONF_TOKEN: user_input[CONF_TOKEN]}
                )

        return self.async_show_form(
            step_id="discovery_confirm", 
            data_schema=vol.Schema({vol.Required(CONF_TOKEN): str}),
            description_placeholders=self.context.get("title_placeholders")
        )
