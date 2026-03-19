"""Constants for the iSmartGate Cloud integration."""

from datetime import timedelta

DOMAIN = "ismartgate_cloud"

CONF_UDI = "udi"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_SCAN_INTERVAL_SECONDS = 10
MIN_SCAN_INTERVAL_SECONDS = 5
MAX_SCAN_INTERVAL_SECONDS = 300

PLATFORMS = ["cover", "sensor"]

DEFAULT_TIMEOUT_SECONDS = 20
DEFAULT_UPDATE_INTERVAL = timedelta(seconds=DEFAULT_SCAN_INTERVAL_SECONDS)
