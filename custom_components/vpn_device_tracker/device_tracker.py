"""VPN Device Tracker device tracker platform."""
import ipaddress
import logging

import voluptuous as vol

from homeassistant.components.device_tracker import PLATFORM_SCHEMA, TrackerEntity
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


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the VPN Device Tracker."""
    source_entity = config.get(CONF_SOURCE_ENTITY)
    ip_zones = config.get(CONF_IP_ZONES, {})
    name = config.get(CONF_NAME)

    if not source_entity or not ip_zones:
        _LOGGER.error("Missing source_entity or ip_zones in configuration")
        return False

    # Validate that source entity exists
    source_state = hass.states.get(source_entity)
    if source_state is None:
        _LOGGER.warning(
            "Source entity %s not found. Entity will be created but may not work until source is available",
            source_entity
        )

    entity = VPNDeviceTracker(hass, source_entity, ip_zones, name)
    async_add_entities([entity], True)
    return True


class VPNDeviceTracker(TrackerEntity):
    """Representation of a VPN Device Tracker."""

    def __init__(self, hass, source_entity, ip_zones, name=None):
        """Initialize the VPN Device Tracker."""
        self._hass = hass
        self._source = source_entity
        self._ip_zones = {}
        self._state = STATE_NOT_HOME
        
        # Use custom name if provided, otherwise generate one
        if name:
            self._attr_name = name
        else:
            self._attr_name = f"VPN Zone {source_entity.replace('device_tracker.', '')}"
        
        self._attr_unique_id = f"vpn_device_tracker_{source_entity}"
        self._attr_should_poll = False
        
        # Parse IP zones with error handling
        for zone, network in ip_zones.items():
            try:
                self._ip_zones[zone] = ipaddress.ip_network(network)
            except ValueError as err:
                _LOGGER.error("Invalid IP network '%s' for zone '%s': %s", network, zone, err)

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._attr_unique_id

    @property
    def name(self):
        """Return the name of the entity."""
        return self._attr_name

    @property
    def state(self):
        """Return the state of the device tracker."""
        return self._state

    @property
    def icon(self):
        """Return the icon."""
        if self._state == STATE_NOT_HOME:
            return "mdi:vpn-off"
        return "mdi:vpn"

    @property
    def extra_state_attributes(self):
        """Return extra attributes."""
        return {
            "source_entity": self._source,
            "configured_zones": list(self._ip_zones.keys()),
        }

    async def async_added_to_hass(self):
        """Register callbacks when entity is added."""
        # Initial update
        await self._async_update_from_source()

        # Track state changes
        @callback
        def state_changed_listener(event):
            """Handle state changes of the source entity."""
            self.hass.async_create_task(self._async_update_from_source())

        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [self._source], state_changed_listener
            )
        )

    async def _async_update_from_source(self):
        """Update state based on source entity."""
        source_state = self.hass.states.get(self._source)
        
        if source_state is None:
            _LOGGER.debug("Source entity %s not available", self._source)
            self._state = STATE_NOT_HOME
            self.async_write_ha_state()
            return

        ip = source_state.attributes.get("ip")
        if not ip:
            _LOGGER.debug("No IP attribute found in %s", self._source)
            self._state = STATE_NOT_HOME
            self.async_write_ha_state()
            return

        try:
            ip_addr = ipaddress.ip_address(ip)
        except ValueError as err:
            _LOGGER.warning("Invalid IP address '%s' from %s: %s", ip, self._source, err)
            self._state = STATE_NOT_HOME
            self.async_write_ha_state()
            return

        # Check which zone the IP belongs to
        matched = STATE_NOT_HOME
        for zone, network in self._ip_zones.items():
            if ip_addr in network:
                matched = zone
                _LOGGER.debug("IP %s matched zone '%s' (network: %s)", ip, zone, network)
                break

        if matched == STATE_NOT_HOME:
            _LOGGER.debug("IP %s did not match any configured zone", ip)

        self._state = matched
        self.async_write_ha_state()
