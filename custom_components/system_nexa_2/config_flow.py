"""Config flow for System Nexa 2 integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_TOKEN
from homeassistant.data_entry_flow import FlowResult
from homeassistant.components import zeroconf

from .const import DOMAIN
from .api import SystemNexa2Client

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_TOKEN): str,
    }
)

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for System Nexa 2."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            # Validate the connection
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
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_zeroconf(
        self, discovery_info: zeroconf.ZeroconfServiceInfo
    ) -> FlowResult:
        """Handle zeroconf discovery."""
        host = discovery_info.host
        self.context["host_ip"] = host
        
        # Check if already configured
        await self.async_set_unique_id(discovery_info.hostname)
        self._abort_if_unique_id_configured(updates={CONF_HOST: host})
        
        self.context["title_placeholders"] = {"name": discovery_info.hostname}
        
        return await self.async_step_discovery_confirm()

    async def async_step_discovery_confirm(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle user confirmation of discovery."""
        host = self.context.get("host_ip")
        errors: dict[str, str] = {}
        
        if user_input is not None:
             # Validate the connection
            client = SystemNexa2Client(host, user_input[CONF_TOKEN])
            try:
                await client.async_get_state()
            except Exception:
                _LOGGER.exception("Failed to connect to System Nexa 2")
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=f"Nexa 2 ({host})", 
                    data={CONF_HOST: host, CONF_TOKEN: user_input[CONF_TOKEN]}
                )

        schema = vol.Schema({vol.Required(CONF_TOKEN): str})
        return self.async_show_form(
            step_id="discovery_confirm", 
            data_schema=schema, 
            errors=errors,
            description_placeholders={"host": host}
        )
