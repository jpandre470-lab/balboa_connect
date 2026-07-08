"""Const file for Balboa Connect."""
import logging

_LOGGER = logging.getLogger(__name__)
CONF_SYNC_TIME = "sync_time"
CONF_KEEPALIVE_ENABLED = "keepalive_enabled"
CONF_KEEPALIVE_INTERVAL = "keepalive_interval"
CONF_KEEPALIVE_FRAME_TYPE = "keepalive_frame_type"
CONF_SOCKET_TIMEOUT = "socket_timeout"
DATA_LISTENER = "listener"
DEFAULT_SCAN_INTERVAL = 1
# Keep-alive is opt-in: the spa already pushes status updates on its own,
# so the integration stays passive on the connection unless the user
# explicitly enables an active keep-alive.
DEFAULT_KEEPALIVE_ENABLED = False
DEFAULT_KEEPALIVE_INTERVAL = 30
DEFAULT_SOCKET_TIMEOUT = 30

# Keep-alive frame types
# - "minimal": the bare \x0a\xbf\x00\x00\x01 frame, no response expected from the module.
# - "existing_client_request": \x0a\xbf\x04 (Existing Client Request), which makes the
#   WiFi module reply with a Configuration Response (0x94) — a real proof of life.
KEEPALIVE_FRAME_MINIMAL = "minimal"
KEEPALIVE_FRAME_EXISTING_CLIENT = "existing_client_request"
KEEPALIVE_FRAME_TYPES = [KEEPALIVE_FRAME_EXISTING_CLIENT, KEEPALIVE_FRAME_MINIMAL]
DEFAULT_KEEPALIVE_FRAME_TYPE = KEEPALIVE_FRAME_EXISTING_CLIENT
DOMAIN = "balboa_connect"
FILTER_CYCLE_TIMES = ["Begins", "Runs"]
MIN_SCAN_INTERVAL = 1
MIN_KEEPALIVE_INTERVAL = 1
MAX_KEEPALIVE_INTERVAL = 3600
MIN_SOCKET_TIMEOUT = 5
MAX_SOCKET_TIMEOUT = 3600
SPA = "spa"

SPACLIENT_COMPONENTS = [
    "binary_sensor",
    "climate",
    "light",
    "number",
    "select",
    "sensor",
    "switch",
    "time",
]

FAULT_MSG = {
    15: "Sensors are out of sync",
    16: "The water flow is low",
    17: "The water flow has failed",
    18: "The settings have been reset",
    19: "Priming Mode",
    20: "The clock has failed",
    21: "The settings have been reset",
    22: "Program memory failure",
    26: "Sensors are out of sync -- Call for service",
    27: "The heater is dry",
    28: "The heater may be dry",
    29: "The water is too hot",
    30: "The heater is too hot",
    31: "Sensor A Fault",
    32: "Sensor B Fault",
    34: "A pump may be stuck on",
    35: "Hot fault",
    36: "The GFCI test failed",
    37: "Standby Mode (Hold Mode)"
}

ICONS = {
    "Auxiliary 1": "mdi:numeric-1-circle-outline",
    "Auxiliary 2": "mdi:numeric-2-circle-outline",
    "Blower": "mdi:weather-windy",
    "Circulation Pump": "mdi:pump",
    "Cleanup Cycle": "mdi:broom",
    "Clock Mode": "mdi:clock-outline",
    "Fault Log": "mdi:archive-alert",
    "Filter Cycle": "mdi:sync",
    "GFCI Test": "mdi:shield-check",
    "Heat Mode": "mdi:alpha-r-box-outline",
    "Heating State": "mdi:fire",
    "Heater Voltage": "mdi:flash",
    "Heater Type": "mdi:water-boiler",
    "Hold Mode": "mdi:car-brake-hold",
    "M8 AI": "mdi:robot",
    "Mister": "mdi:auto-fix",
    "Model Name": "mdi:information-outline",
    "Notification": "mdi:bell",
    "Panel Lock": "mdi:lock",
    "Priming": "mdi:pump",
    "Pump 1": "mdi:pump",
    "Pump 2": "mdi:pump",
    "Pump 3": "mdi:pump",
    "Pump 4": "mdi:pump",
    "Pump 5": "mdi:pump",
    "Pump 6": "mdi:pump",
    "Reminder Type": "mdi:reminder",
    "Reminders": "mdi:bell-ring",
    "Sensor A Temperature": "mdi:thermometer",
    "Sensor B Temperature": "mdi:thermometer",
    "Settings Lock": "mdi:lock-outline",
    "Software Version": "mdi:tag",
    "Spa State": "mdi:hot-tub",
    "Spa Thermostat": "mdi:hot-tub",
    "Spa Time": "mdi:clock-digital",
    "Standby Mode": "mdi:ungroup",
    "Temperature Range": "mdi:thermometer-lines",
    "Temperature Scale": "mdi:thermometer-auto",
    "WiFi State": "mdi:wifi",
    "Flip Screen": "mdi:screen-rotation",
}
