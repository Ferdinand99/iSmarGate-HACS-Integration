"""Coordinator for iSmartGate Cloud."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    ISmartGateApiError,
    ISmartGateCloudApi,
    ISmartGateInfo,
    ISmartGateInvalidApiCodeError,
)


class ISmartGateCloudCoordinator(DataUpdateCoordinator[ISmartGateInfo]):
    """Data coordinator for cloud data."""

    def __init__(self, hass, logger, api: ISmartGateCloudApi, update_interval: timedelta) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            logger,
            name="iSmartGate Cloud",
            update_interval=update_interval,
        )
        self.api = api

    async def _async_update_data(self) -> ISmartGateInfo:
        """Fetch latest state from cloud API."""
        try:
            return await self.api.async_get_info()
        except ISmartGateApiError as err:
            raise UpdateFailed(str(err)) from err

    def get_door(self, door_id: int):
        """Get door data by ID from current coordinator state."""
        if self.data is None:
            return None
        for door in self.data.doors:
            if door.door_id == door_id:
                return door
        return None

    async def async_ensure_state(self, door_id: int, target_state: str) -> None:
        """Ensure a door is in target state (opened/closed)."""
        door = self.get_door(door_id)
        if door is None:
            raise UpdateFailed(f"Door {door_id} not found")

        current = door.status
        if current == target_state:
            return

        if not door.apicode:
            raise UpdateFailed(f"Door {door_id} missing API code")

        try:
            await self.api.async_activate(door_id, door.apicode)
        except ISmartGateInvalidApiCodeError:
            # Refresh once to get updated API code, then retry.
            await self.async_request_refresh()
            refreshed = self.get_door(door_id)
            if refreshed is None or not refreshed.apicode:
                raise UpdateFailed(f"Door {door_id} API code refresh failed")
            await self.api.async_activate(door_id, refreshed.apicode)

        # Always refresh after a command so state converges quickly.
        await self.async_request_refresh()
