"""VPN Device Tracker device tracker platform."""
import ipaddress
import logging

from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.const import CONF_NAME, STATE_HOME, STATE_NOT_HOME

from .const import DOMAIN, CONF_SOURCE_ENTITY, CONF_IP_ZONES

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up VPN Device Tracker from a config entry."""
    source_entity = entry.data[CONF_SOURCE_ENTITY]
    ip_zones = entry.data[CONF_IP_ZONES]
    name = entry.data.get(CONF_NAME)

    # Parse IP zones
    parsed_zones = {}
    for zone, network in ip_zones.items():
        try:
            parsed_zones[zone] = ipaddress.ip_network(network)
        except ValueError as err:
            _LOGGER.error("Invalid IP network '%s' for zone '%s': %s", network, zone, err)

    if not parsed_zones:
        _LOGGER.error("No valid IP zones configured")
        return

    entity = VPNDeviceTracker(hass, entry.entry_id, source_entity, parsed_zones, name)
    async_add_entities([entity], True)


class VPNDeviceTracker(TrackerEntity):
    """Representation of a VPN Device Tracker."""

    _attr_has_entity_name = False
    _attr_should_poll = False

    def __init__(self, hass, entry_id, source_entity, ip_zones, name=None):
        """Initialize the VPN Device Tracker."""
        self._source = source_entity
        self._ip_zones = ip_zones
        self._state = STATE_NOT_HOME
        self._ip_address = None
        
        # Generate entity details
        source_clean = source_entity.replace('device_tracker.', '')
        self._attr_unique_id = f"{DOMAIN}_{source_clean}"
        
        if name:
            self._attr_name = name
        else:
            self._attr_name = f"VPN Zone {source_clean}"

        _LOGGER.info("VPN Device Tracker initialized for %s", source_entity)

    @property
    def state(self):
        """Return the state of the device tracker."""
        return self._state

    @property
    def location_name(self):
        """Return the location name of the device."""
        return self._state if self._state != STATE_NOT_HOME else None

    @property
    def icon(self):
        """Return the icon."""
        if self._state == STATE_NOT_HOME:
            return "mdi:vpn-off"
        return "mdi:vpn"

    @property
    def extra_state_attributes(self):
        """Return extra attributes."""
        attrs = {
            "source_entity": self._source,
            "configured_zones": list(self._ip_zones.keys()),
        }
        if self._ip_address:
            attrs["ip_address"] = self._ip_address
        return attrs

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
            self._ip_address = None
            self.async_write_ha_state()
            return

        ip = source_state.attributes.get("ip")
        if not ip:
            _LOGGER.debug("No IP attribute found in %s", self._source)
            self._state = STATE_NOT_HOME
            self._ip_address = None
            self.async_write_ha_state()
            return

        self._ip_address = ip

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
