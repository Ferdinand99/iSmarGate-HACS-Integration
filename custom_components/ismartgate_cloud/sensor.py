"""Sensor platform for iSmartGate Cloud."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    """Set up sensors for each enabled door."""
    coordinator = entry.runtime_data
    entities = []

    if coordinator.data is None:
        return

    for door in coordinator.data.doors:
        if not door.enabled:
            continue
        entities.append(ISmartGateBatterySensor(entry, coordinator, door.door_id))
        entities.append(ISmartGateTemperatureSensor(entry, coordinator, door.door_id))

    async_add_entities(entities)


class _ISmartGateBaseSensor(CoordinatorEntity, SensorEntity):
    """Shared base for iSmartGate sensors."""

    _attr_should_poll = False

    def __init__(self, entry, coordinator, door_id: int) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._door_id = door_id

    @property
    def _door(self):
        return self.coordinator.get_door(self._door_id)

    @property
    def device_info(self) -> DeviceInfo:
        """Attach sensor entities to the same device as the cover entity."""
        info = self.coordinator.data
        return DeviceInfo(
            identifiers={(DOMAIN, str(self._entry.unique_id))},
            name=info.name if info else "iSmartGate",
            manufacturer="iSmartGate",
            model=info.model if info else "unknown",
            sw_version=info.firmware_version if info else "unknown",
        )


class ISmartGateBatterySensor(_ISmartGateBaseSensor):
    """Battery sensor per door."""

    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, entry, coordinator, door_id: int) -> None:
        super().__init__(entry, coordinator, door_id)
        self._attr_unique_id = f"{entry.unique_id}_door_{door_id}_battery"

    @property
    def name(self) -> str:
        return f"Door {self._door_id} battery"

    @property
    def available(self) -> bool:
        door = self._door
        return super().available and door is not None and door.voltage is not None

    @property
    def native_value(self):
        door = self._door
        return door.voltage if door else None


class ISmartGateTemperatureSensor(_ISmartGateBaseSensor):
    """Temperature sensor per door."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, entry, coordinator, door_id: int) -> None:
        super().__init__(entry, coordinator, door_id)
        self._attr_unique_id = f"{entry.unique_id}_door_{door_id}_temperature"

    @property
    def name(self) -> str:
        return f"Door {self._door_id} temperature"

    @property
    def available(self) -> bool:
        door = self._door
        return super().available and door is not None and door.temperature is not None

    @property
    def native_value(self):
        door = self._door
        return door.temperature if door else None
