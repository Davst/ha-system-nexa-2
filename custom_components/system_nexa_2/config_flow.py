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
        from zeroconf import ServiceBrowser, ServiceStateChange

        results = {}

        def on_service_state_change(zeroconf, service_type, name, state_change):
            if state_change is ServiceStateChange.Added:
                info = zeroconf.get_service_info(service_type, name)
                if info:
                    results[name] = info

        try:
            zc = await zeroconf.async_get_instance(self.hass)
            browser = ServiceBrowser(zc, "_systemnexa2._tcp.local.", handlers=[on_service_state_change])
            
            # Wait a few seconds for discovery
            import asyncio
            await asyncio.sleep(3)
            
            browser.cancel()
            
        except Exception as e:
            _LOGGER.warning("Error during active mDNS scan: %s", e)

        # Update cache/discovered list with active findings
        # For simplicity, we just pass what we found to the cache (if we were using one)
        # or merge it with pick_device logic.
        # But wait, pick_device uses `self._discovered_devices`.
        # We should pre-populate it here.
        
        self._discovered_devices = {}
        for name, info in results.items():
            # Conversion logic similar to pick_device loop
            dev_name = name.replace("._systemnexa2._tcp.local.", "")
            model = "Nexa Device"
            local_id = None
            
            props = {k.decode(): v.decode() if isinstance(v, bytes) else v for k,v in info.properties.items()}
            if "model" in props: 
                model = props["model"]
            
            # Use IP
            host = info.parsed_addresses()[0] if info.parsed_addresses() else None
            
            if host:
                label = f"{dev_name} ({model}) - {host}"
                self._discovered_devices[label] = info

        # Now pass to pick_device. 
        # But pick_device re-scans using cache. 
        # We should modify pick_device to accept pre-filled devices or use self._discovered_devices.
        # Let's verify pick_device logic.
        
        return await self.async_step_pick_device()

    async def async_step_pick_device(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Allow the user to pick a device."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            if user_input["device"] == "refresh":
                 return await self.async_step_pick_device()
            if user_input["device"] == "manual":
                 return await self.async_step_manual()
            
            # Selected a device
            host = self._discovered_devices[user_input["device"]].host
            self.context["host"] = host
            self.context["title_placeholders"] = {"name": user_input["device"]}
            return await self.async_step_token_entry()

        # Gather devices
        # We rely on HA's zeroconf to have found things.
        
        # HaZeroconf doesn't support get_service_info_list directly.
        # We rely on the async_step_zeroconf to trigger flows automatically.
        # This step essentially just checks if we have any "pending" discoveries if we could, 
        # but since we can't easily query the cache, we'll just show the manual option.
        services = []
        
        # If we came from search, we might already have devices
        if not self._discovered_devices:
             self._discovered_devices = {}
        
        # If we found nothing new via cache logic (which is empty now), we rely on what we have.
        
        options = {}
        for label, service in self._discovered_devices.items():
             options[label] = label

        # Legacy active-scan-in-pick-device logic was here, but we moved it to async_step_search
        # and we cleared the list here previously. 
        # Now we just list what's in self._discovered_devices.
        
        if not options:
            errors["base"] = "no_devices_found"

        # Add options
        options["refresh"] = "Refresh List"
        options["manual"] = "Enter Manually"

        return self.async_show_form(
            step_id="pick_device",
            data_schema=vol.Schema({
                vol.Required("device", default=list(options.keys())[0]): vol.In(options)
            }),
            errors=errors
        )

    async def async_step_manual(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle manual entry."""
        errors: dict[str, str] = {}
        if user_input is not None:
             client = SystemNexa2Client(user_input[CONF_HOST], user_input.get(CONF_TOKEN, ""))
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
             data_schema=vol.Schema({vol.Optional(CONF_TOKEN, default=""): str}),
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
        host = self.context.get("host")
        
        # If this is the first time we enter this step (user_input is None),
        # try to connect with an empty token immediately (Auto-Connect).
        if user_input is None:
            # Attempt auto-connect with empty token
            client = SystemNexa2Client(host, "")
            try:
                await client.async_get_state()
                # If successful, we create the entry immediately!
                return self.async_create_entry(
                   title=f"Nexa 2 ({host})", 
                   data={CONF_HOST: host, CONF_TOKEN: ""}
                )
            except Exception:
                # If failed (e.g. 401 Auth Required), we fall through to showing the form.
                # We log this as debug so we know why we are showing form.
                _LOGGER.debug("Auto-connect with empty token failed, prompting user for token")

        errors: dict[str, str] = {}
        if user_input is not None:
             client = SystemNexa2Client(host, user_input.get(CONF_TOKEN, ""))
             try:
                await client.async_get_state()
             except Exception:
                _LOGGER.exception("Failed to connect to System Nexa 2")
                errors = {"base": "cannot_connect"}
             else:
                return self.async_create_entry(
                    title=f"Nexa 2 ({host})", 
                    data={CONF_HOST: host, CONF_TOKEN: user_input.get(CONF_TOKEN, "")}
                )

        return self.async_show_form(
            step_id="discovery_confirm", 
            data_schema=vol.Schema({vol.Optional(CONF_TOKEN): str}),
            description_placeholders=self.context.get("title_placeholders"),
            errors=errors
        )
