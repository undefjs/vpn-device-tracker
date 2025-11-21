"""Config flow for VPN Device Tracker integration."""
import ipaddress
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, CONF_SOURCE_ENTITY, CONF_IP_ZONES

_LOGGER = logging.getLogger(__name__)


class VPNDeviceTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for VPN Device Tracker."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Validate source entity exists
            source_entity = user_input[CONF_SOURCE_ENTITY]
            if not self.hass.states.get(source_entity):
                errors["source_entity"] = "entity_not_found"
            
            # Validate IP zones
            ip_zones_text = user_input.get(CONF_IP_ZONES, "")
            ip_zones = {}
            
            try:
                for line in ip_zones_text.strip().split("\n"):
                    if line.strip() and ":" in line:
                        zone_name, network = line.split(":", 1)
                        zone_name = zone_name.strip()
                        network = network.strip()
                        
                        # Validate network
                        try:
                            ipaddress.ip_network(network)
                            ip_zones[zone_name] = network
                        except ValueError:
                            errors["ip_zones"] = "invalid_network"
                            break
                
                if not ip_zones and not errors:
                    errors["ip_zones"] = "no_zones"
                    
            except Exception:
                errors["ip_zones"] = "invalid_format"

            if not errors:
                # Create unique ID from source entity
                await self.async_set_unique_id(f"{DOMAIN}_{source_entity}")
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=user_input.get(CONF_NAME, f"VPN Zone {source_entity}"),
                    data={
                        CONF_SOURCE_ENTITY: source_entity,
                        CONF_IP_ZONES: ip_zones,
                        CONF_NAME: user_input.get(CONF_NAME, ""),
                    },
                )

        # Show configuration form
        data_schema = vol.Schema({
            vol.Required(CONF_SOURCE_ENTITY): cv.entity_id,
            vol.Required(CONF_IP_ZONES): str,
            vol.Optional(CONF_NAME): str,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "example": "home: 192.168.1.0/24\noffice: 10.20.0.0/16"
            },
        )
