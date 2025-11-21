"""Config flow for VPN Device Tracker integration."""
import ipaddress
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, CONF_SOURCE_ENTITY, CONF_IP_ZONES

_LOGGER = logging.getLogger(__name__)


class VPNDeviceTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for VPN Device Tracker."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self._source_entity = None
        self._name = None
        self._ip_zones = {}

    async def async_step_user(self, user_input=None):
        """Handle the initial step - select source entity."""
        errors = {}

        if user_input is not None:
            source_entity = user_input[CONF_SOURCE_ENTITY]
            
            # Validate source entity exists
            if not self.hass.states.get(source_entity):
                errors["source_entity"] = "entity_not_found"
            else:
                self._source_entity = source_entity
                self._name = user_input.get(CONF_NAME, "")
                return await self.async_step_add_zone()

        data_schema = vol.Schema({
            vol.Required(CONF_SOURCE_ENTITY): str,
            vol.Optional(CONF_NAME, default=""): str,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "source_example": "device_tracker.mi_movil"
            },
        )

    async def async_step_add_zone(self, user_input=None):
        """Handle adding a zone."""
        errors = {}

        if user_input is not None:
            zone_name = user_input.get("zone_name", "").strip()
            zone_network = user_input.get("zone_network", "").strip()

            # Validate inputs
            if not zone_name:
                errors["zone_name"] = "zone_name_required"
            elif zone_name in self._ip_zones:
                errors["zone_name"] = "zone_already_exists"
            
            if not zone_network:
                errors["zone_network"] = "zone_network_required"
            else:
                try:
                    ipaddress.ip_network(zone_network)
                except ValueError:
                    errors["zone_network"] = "invalid_network"

            if not errors:
                # Add the zone
                self._ip_zones[zone_name] = zone_network
                
                # Ask if user wants to add more zones
                return await self.async_step_add_more()

        # Show current zones
        zones_list = "\n".join([f"✓ {name}: {net}" for name, net in self._ip_zones.items()])
        description = f"Source: {self._source_entity}\n\nZonas configuradas:\n{zones_list}" if self._ip_zones else f"Source: {self._source_entity}\n\nAñade la primera zona"

        data_schema = vol.Schema({
            vol.Required("zone_name"): str,
            vol.Required("zone_network"): str,
        })

        return self.async_show_form(
            step_id="add_zone",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "configured": description,
                "name_example": "home, office, parents, etc.",
                "network_example": "192.168.1.0/24"
            },
        )

    async def async_step_add_more(self, user_input=None):
        """Ask if user wants to add more zones."""
        if user_input is not None:
            if user_input.get("add_more"):
                return await self.async_step_add_zone()
            else:
                # Finish configuration
                if not self._ip_zones:
                    return await self.async_step_add_zone()
                
                # Create unique ID
                await self.async_set_unique_id(f"{DOMAIN}_{self._source_entity}")
                self._abort_if_unique_id_configured()

                title = self._name or f"VPN Zone {self._source_entity.replace('device_tracker.', '')}"
                
                return self.async_create_entry(
                    title=title,
                    data={
                        CONF_SOURCE_ENTITY: self._source_entity,
                        CONF_IP_ZONES: self._ip_zones,
                        CONF_NAME: self._name,
                    },
                )

        zones_list = "\n".join([f"✓ {name}: {net}" for name, net in self._ip_zones.items()])
        
        data_schema = vol.Schema({
            vol.Required("add_more", default=True): bool,
        })

        return self.async_show_form(
            step_id="add_more",
            data_schema=data_schema,
            description_placeholders={
                "zones": zones_list,
                "count": str(len(self._ip_zones))
            },
        )
