"""The iSmartGate Cloud integration."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ISmartGateAuthError, ISmartGateCloudApi
from .const import (
    CONF_SCAN_INTERVAL,
    CONF_UDI,
    DEFAULT_SCAN_INTERVAL_SECONDS,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import ISmartGateCloudCoordinator

_LOGGER = logging.getLogger(__name__)


type ISmartGateCloudConfigEntry = ConfigEntry[ISmartGateCloudCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: ISmartGateCloudConfigEntry) -> bool:
    """Set up iSmartGate Cloud from config entry."""
    session = async_get_clientsession(hass)

    udi = entry.data[CONF_UDI]
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]

    scan_interval = entry.options.get(
        CONF_SCAN_INTERVAL,
        entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_SECONDS),
    )

    api = ISmartGateCloudApi(
        session=session,
        udi=udi,
        username=username,
        password=password,
    )
    coordinator = ISmartGateCloudCoordinator(
        hass=hass,
        logger=_LOGGER,
        api=api,
        update_interval=timedelta(seconds=int(scan_interval)),
    )

    try:
        await coordinator.async_config_entry_first_refresh()
    except ISmartGateAuthError as err:
        raise ConfigEntryNotReady(f"Authentication failed: {err}") from err
    except Exception as err:
        raise ConfigEntryNotReady(f"Unable to connect: {err}") from err

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ISmartGateCloudConfigEntry) -> bool:
    """Unload config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
