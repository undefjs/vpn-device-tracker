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

DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_SOURCE_ENTITY): str,
    vol.Required(CONF_IP_ZONES): str,
    vol.Optional(CONF_NAME, default=""): str,
})


async def validate_input(hass: HomeAssistant, data: dict):
    """Validate the user input."""
    source_entity = data[CONF_SOURCE_ENTITY]
    ip_zones_text = data[CONF_IP_ZONES]
    
    # Validate source entity exists
    if not hass.states.get(source_entity):
        raise EntityNotFound
    
    # Validate and parse IP zones
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
                except ValueError as err:
                    _LOGGER.error("Invalid network %s: %s", network, err)
                    raise InvalidNetwork
        
        if not ip_zones:
            raise NoZones
            
    except (ValueError, AttributeError) as err:
        _LOGGER.error("Invalid IP zones format: %s", err)
        raise InvalidFormat

    return {
        "title": data.get(CONF_NAME) or f"VPN Zone {source_entity.replace('device_tracker.', '')}",
        "ip_zones": ip_zones
    }


class VPNDeviceTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for VPN Device Tracker."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                
                # Create unique ID from source entity
                await self.async_set_unique_id(f"{DOMAIN}_{user_input[CONF_SOURCE_ENTITY]}")
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=info["title"],
                    data={
                        CONF_SOURCE_ENTITY: user_input[CONF_SOURCE_ENTITY],
                        CONF_IP_ZONES: info["ip_zones"],
                        CONF_NAME: user_input.get(CONF_NAME, ""),
                    },
                )
            except EntityNotFound:
                errors["source_entity"] = "entity_not_found"
            except InvalidNetwork:
                errors["ip_zones"] = "invalid_network"
            except InvalidFormat:
                errors["ip_zones"] = "invalid_format"
            except NoZones:
                errors["ip_zones"] = "no_zones"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                "example": "home: 192.168.1.0/24\noffice: 10.20.0.0/16"
            },
        )


class EntityNotFound(HomeAssistantError):
    """Error to indicate entity not found."""


class InvalidNetwork(HomeAssistantError):
    """Error to indicate invalid network format."""


class InvalidFormat(HomeAssistantError):
    """Error to indicate invalid format."""


class NoZones(HomeAssistantError):
    """Error to indicate no zones provided."""
