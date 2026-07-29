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

# LED color cycling
# The LED units have no direct "set color" command; color is selected by
# rapidly toggling power a fixed number of times (reverse-engineered from
# physical behavior, not documented in the protocol wiki).
CONF_LIGHT_MODE = "light_mode"
LIGHT_MODE_SWITCH = "switch"
LIGHT_MODE_COLOR = "color"
DEFAULT_LIGHT_MODE = LIGHT_MODE_SWITCH

CONF_LED_COLORS = "led_colors"
CONF_LED_DELAY_ON = "led_delay_on"
CONF_LED_DELAY_OFF = "led_delay_off"
CONF_LED_DELAY_RESET = "led_delay_reset"
DEFAULT_LED_DELAY_ON = 500      # ms - pause after switching on, before switching off again
DEFAULT_LED_DELAY_OFF = 500     # ms - pause after switching off, before switching on again
DEFAULT_LED_DELAY_RESET = 3     # seconds - pause used to reset the color cycle back to color 1
MIN_LED_DELAY_MS = 100
MAX_LED_DELAY_MS = 5000
MIN_LED_DELAY_RESET = 1
MAX_LED_DELAY_RESET = 60

LED_COLOR_NAME = "name"
LED_COLOR_CYCLES = "cycles"
LED_COLOR_RGB = "rgb"
LIGHT_OFF = "Off"

DEFAULT_LED_COLORS = [
    {LED_COLOR_NAME: "Red",    LED_COLOR_CYCLES: 1, LED_COLOR_RGB: [255, 0,   0]},
    {LED_COLOR_NAME: "Green",  LED_COLOR_CYCLES: 2, LED_COLOR_RGB: [0,   255, 0]},
    {LED_COLOR_NAME: "Blue",   LED_COLOR_CYCLES: 3, LED_COLOR_RGB: [0,   0,   255]},
    {LED_COLOR_NAME: "Yellow", LED_COLOR_CYCLES: 4, LED_COLOR_RGB: [255, 255, 0]},
    {LED_COLOR_NAME: "Cyan",   LED_COLOR_CYCLES: 5, LED_COLOR_RGB: [0,   255, 255]},
    {LED_COLOR_NAME: "Pink",   LED_COLOR_CYCLES: 6, LED_COLOR_RGB: [255, 105, 180]},
    {LED_COLOR_NAME: "White",  LED_COLOR_CYCLES: 7, LED_COLOR_RGB: [255, 255, 255]},
    {LED_COLOR_NAME: "Random", LED_COLOR_CYCLES: 8, LED_COLOR_RGB: [128, 128, 128]},
]


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
    "Light Color": "mdi:led-strip-variant",
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
