"""VPN Device Tracker device tracker platform."""
import ipaddress
import logging

import voluptuous as vol

from homeassistant.components.device_tracker import PLATFORM_SCHEMA
from homeassistant.components.device_tracker.const import (
    DOMAIN as DEVICE_TRACKER_DOMAIN,
    SOURCE_TYPE_ROUTER,
)
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.const import CONF_NAME, STATE_HOME, STATE_NOT_HOME
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

DOMAIN = "vpn_device_tracker"

CONF_SOURCE_ENTITY = "source_entity"
CONF_IP_ZONES = "ip_zones"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_SOURCE_ENTITY): cv.entity_id,
    vol.Required(CONF_IP_ZONES): vol.Schema({cv.string: cv.string}),
    vol.Optional(CONF_NAME): cv.string,
})


async def async_setup_scanner(hass, config, async_see, discovery_info=None):
    """Set up the VPN Device Tracker scanner."""
    source_entity = config.get(CONF_SOURCE_ENTITY)
    ip_zones = config.get(CONF_IP_ZONES, {})
    device_name = config.get(CONF_NAME)

    if not source_entity or not ip_zones:
        _LOGGER.error("Missing source_entity or ip_zones in configuration")
        return False

    # Parse IP zones with error handling
    parsed_zones = {}
    for zone, network in ip_zones.items():
        try:
            parsed_zones[zone] = ipaddress.ip_network(network)
        except ValueError as err:
            _LOGGER.error("Invalid IP network '%s' for zone '%s': %s", network, zone, err)

    if not parsed_zones:
        _LOGGER.error("No valid IP zones configured")
        return False

    # Validate that source entity exists
    source_state = hass.states.get(source_entity)
    if source_state is None:
        _LOGGER.warning(
            "Source entity %s not found. Tracker will be created but may not work until source is available",
            source_entity
        )

    scanner = VPNDeviceScanner(
        hass, async_see, source_entity, parsed_zones, device_name
    )
    
    # Initial update
    await scanner.async_update()

    return True


class VPNDeviceScanner:
    """VPN Device Scanner that monitors source entity and updates location."""

    def __init__(self, hass, async_see, source_entity, ip_zones, device_name=None):
        """Initialize the scanner."""
        self.hass = hass
        self.async_see = async_see
        self._source = source_entity
        self._ip_zones = ip_zones
        
        # Generate device name and ID
        source_clean = source_entity.replace('device_tracker.', '')
        self._device_id = f"vpn_zone_{source_clean}"
        self._device_name = device_name or f"VPN Zone {source_clean}"
        
        # Set up state change listener
        async_track_state_change_event(
            hass, [source_entity], self._async_state_changed_listener
        )
        
        _LOGGER.info("VPN Device Tracker initialized for %s", source_entity)

    @callback
    def _async_state_changed_listener(self, event):
        """Handle state changes of the source entity."""
        self.hass.async_create_task(self.async_update())

    async def async_update(self):
        """Update the device location based on IP."""
        source_state = self.hass.states.get(self._source)
        
        if source_state is None:
            _LOGGER.debug("Source entity %s not available", self._source)
            await self.async_see(
                dev_id=self._device_id,
                host_name=self._device_name,
                location_name=STATE_NOT_HOME,
                source_type=SOURCE_TYPE_ROUTER,
            )
            return

        ip = source_state.attributes.get("ip")
        if not ip:
            _LOGGER.debug("No IP attribute found in %s", self._source)
            await self.async_see(
                dev_id=self._device_id,
                host_name=self._device_name,
                location_name=STATE_NOT_HOME,
                source_type=SOURCE_TYPE_ROUTER,
            )
            return

        try:
            ip_addr = ipaddress.ip_address(ip)
        except ValueError as err:
            _LOGGER.warning("Invalid IP address '%s' from %s: %s", ip, self._source, err)
            await self.async_see(
                dev_id=self._device_id,
                host_name=self._device_name,
                location_name=STATE_NOT_HOME,
                source_type=SOURCE_TYPE_ROUTER,
            )
            return

        # Check which zone the IP belongs to
        matched_zone = None
        for zone, network in self._ip_zones.items():
            if ip_addr in network:
                matched_zone = zone
                _LOGGER.debug("IP %s matched zone '%s' (network: %s)", ip, zone, network)
                break

        if matched_zone is None:
            matched_zone = STATE_NOT_HOME
            _LOGGER.debug("IP %s did not match any configured zone", ip)

        # Update the device tracker
        await self.async_see(
            dev_id=self._device_id,
            host_name=self._device_name,
            location_name=matched_zone,
            source_type=SOURCE_TYPE_ROUTER,
            attributes={
                "source_entity": self._source,
                "ip_address": str(ip),
                "configured_zones": list(self._ip_zones.keys()),
            },
        )
