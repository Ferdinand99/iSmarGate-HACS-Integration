"""Cover platform for iSmartGate Cloud."""

from __future__ import annotations

from homeassistant.components.cover import (
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.const import CONF_UDI
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    """Set up iSmartGate cloud covers."""
    coordinator = entry.runtime_data
    entities = []

    if coordinator.data is None:
        return

    for door in coordinator.data.doors:
        if door.enabled:
            entities.append(ISmartGateCloudCover(entry, coordinator, door.door_id))

    async_add_entities(entities)


class ISmartGateCloudCover(CoordinatorEntity, CoverEntity):
    """iSmartGate cloud cover entity."""

    _attr_supported_features = CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE

    def __init__(self, entry, coordinator, door_id: int) -> None:
        """Initialize cover entity."""
        super().__init__(coordinator)
        self._entry = entry
        self._door_id = door_id
        self._attr_unique_id = f"{entry.unique_id}_door_{door_id}"

    @property
    def _door(self):
        return self.coordinator.get_door(self._door_id)

    @property
    def name(self) -> str:
        """Entity name."""
        door = self._door
        if door and door.name:
            return door.name
        return f"Door {self._door_id}"

    @property
    def device_class(self) -> CoverDeviceClass:
        """Set device class by door mode."""
        door = self._door
        if door and door.gate:
            return CoverDeviceClass.GATE
        return CoverDeviceClass.GARAGE

    @property
    def is_closed(self) -> bool | None:
        """Return closed state."""
        door = self._door
        if door is None:
            return None
        if door.status == "closed":
            return True
        if door.status == "opened":
            return False
        return None

    async def async_open_cover(self, **kwargs) -> None:
        """Open door."""
        await self.coordinator.async_ensure_state(self._door_id, "opened")

    async def async_close_cover(self, **kwargs) -> None:
        """Close door."""
        await self.coordinator.async_ensure_state(self._door_id, "closed")

    @property
    def device_info(self) -> DeviceInfo:
        """Device registry info."""
        info = self.coordinator.data
        config_url = f"https://{self._entry.data[CONF_UDI]}.isgaccess.com"
        if info and info.remote_access_enabled and info.remote_access:
            config_url = f"https://{info.remote_access}"

        return DeviceInfo(
            identifiers={(DOMAIN, str(self._entry.unique_id))},
            name=info.name if info else "iSmartGate",
            manufacturer="iSmartGate",
            model=info.model if info else "unknown",
            sw_version=info.firmware_version if info else "unknown",
            configuration_url=config_url,
        )
