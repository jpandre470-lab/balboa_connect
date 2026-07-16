"""Support for Balboa Connect select entities."""
# Import the device class from the component that you want to support
import asyncio
from . import SpaClientDevice
from .const import (
    _LOGGER,
    CONF_LED_COLORS,
    CONF_LED_DELAY_OFF,
    CONF_LED_DELAY_ON,
    CONF_LED_DELAY_RESET,
    CONF_LIGHT_MODE,
    DEFAULT_LED_COLORS,
    DEFAULT_LED_DELAY_OFF,
    DEFAULT_LED_DELAY_ON,
    DEFAULT_LED_DELAY_RESET,
    DEFAULT_LIGHT_MODE,
    DOMAIN,
    ICONS,
    LED_COLOR_CYCLES,
    LED_COLOR_NAME,
    LIGHT_MODE_COLOR,
    LIGHT_OFF,
    SPA,
)
from datetime import timedelta
from homeassistant.components.select import SelectEntity

SCAN_INTERVAL = timedelta(seconds=1)

CLEANUP_CYCLE_OPTIONS = [
    "Off",
    "30 min",
    "60 min",
    "90 min",
    "120 min",
    "150 min",
    "180 min",
    "210 min",
    "240 min",
]


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Setup the Balboa Connect select entities."""

    spaclient = hass.data[DOMAIN][config_entry.entry_id][SPA]
    entities = []

    entities.append(TemperatureScale(spaclient, config_entry))
    entities.append(ClockMode(spaclient, config_entry))
    entities.append(CleanupCycle(spaclient, config_entry))

    # Light color selects only apply in "color" mode. In "switch" mode, the
    # same lights are exposed as plain on/off lights instead (light.py).
    if config_entry.options.get(CONF_LIGHT_MODE, DEFAULT_LIGHT_MODE) == LIGHT_MODE_COLOR:
        light_array = spaclient.get_light_list()
        for i in range(0, 2):
            if light_array[i] != 0:
                entities.append(BalboaLightSelect(i + 1, spaclient, config_entry))

    async_add_entities(entities, True)


class TemperatureScale(SpaClientDevice, SelectEntity):
    """Representation of the Temperature Scale select (°C / °F)."""

    def __init__(self, spaclient, config_entry):
        """Initialize the device."""
        super().__init__(spaclient, config_entry)
        self._spaclient = spaclient
        self._icon = ICONS.get('Temperature Scale')

    @property
    def unique_id(self) -> str:
        return f"{self._spaclient.get_macaddr().replace(':', '')}#temperature_scale"

    @property
    def name(self):
        return 'Temperature Scale'

    @property
    def icon(self):
        return self._icon

    @property
    def options(self):
        return ["Fahrenheit", "Celsius"]

    @property
    def current_option(self):
        return self._spaclient.get_temp_scale()

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        self._spaclient.set_temperature_scale(option)

    @property
    def available(self) -> bool:
        return self._spaclient.get_gateway_status()


class ClockMode(SpaClientDevice, SelectEntity):
    """Representation of the Clock Mode select (12 Hr / 24 Hr)."""

    def __init__(self, spaclient, config_entry):
        """Initialize the device."""
        super().__init__(spaclient, config_entry)
        self._spaclient = spaclient
        self._icon = ICONS.get('Clock Mode')

    @property
    def unique_id(self) -> str:
        return f"{self._spaclient.get_macaddr().replace(':', '')}#clock_mode"

    @property
    def name(self):
        return 'Clock Mode'

    @property
    def icon(self):
        return self._icon

    @property
    def options(self):
        return ["12 Hr", "24 Hr"]

    @property
    def current_option(self):
        return self._spaclient.get_time_scale()

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        self._spaclient.set_clock_mode(option)

    @property
    def available(self) -> bool:
        return self._spaclient.get_gateway_status()


class CleanupCycle(SpaClientDevice, SelectEntity):
    """Representation of the Cleanup Cycle select."""

    def __init__(self, spaclient, config_entry):
        """Initialize the device."""
        super().__init__(spaclient, config_entry)
        self._spaclient = spaclient
        self._icon = ICONS.get('Cleanup Cycle')

    @property
    def unique_id(self) -> str:
        return f"{self._spaclient.get_macaddr().replace(':', '')}#cleanup_cycle"

    @property
    def name(self):
        return 'Cleanup Cycle'

    @property
    def icon(self):
        return self._icon

    @property
    def options(self):
        return CLEANUP_CYCLE_OPTIONS

    @property
    def current_option(self):
        value = self._spaclient.get_pref_clean_up_cycle()
        if value == 0:
            return "Off"
        return f"{value * 30} min"

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        if option == "Off":
            self._spaclient.set_cleanup_cycle(0)
        else:
            # Parse "30 min" -> 1, "60 min" -> 2, etc.
            minutes = int(option.replace(" min", ""))
            self._spaclient.set_cleanup_cycle(minutes // 30)

    @property
    def available(self) -> bool:
        return self._spaclient.get_gateway_status()


class BalboaLightSelect(SpaClientDevice, SelectEntity):
    """Representation of an LED color select.

    The LED units have no direct "set color" command: color is selected by
    rapidly toggling power a fixed number of times, which advances an
    internal color cycle in the LED hardware itself (reverse-engineered
    behavior, not documented in the protocol wiki).
    """

    def __init__(self, light_num, spaclient, config_entry):
        """Initialize the device."""
        super().__init__(spaclient, config_entry)
        self._light_num = light_num
        self._spaclient = spaclient
        self._config_entry = config_entry
        self._icon = ICONS.get('Light Color', 'mdi:led-strip-variant')
        self._current_option = None
        self._cycling = False

    def _get_colors(self):
        return self._config_entry.options.get(CONF_LED_COLORS, DEFAULT_LED_COLORS)

    @property
    def unique_id(self) -> str:
        return f"{self._spaclient.get_macaddr().replace(':', '')}#light_{self._light_num}_color"

    @property
    def name(self):
        return f'Light {self._light_num} Color'

    @property
    def icon(self):
        return self._icon

    @property
    def options(self):
        return [c[LED_COLOR_NAME] for c in self._get_colors()] + [LIGHT_OFF]

    @property
    def current_option(self):
        if not self._spaclient.get_light(self._light_num):
            return LIGHT_OFF
        return self._current_option or LIGHT_OFF

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        if self._cycling:
            return
        self._cycling = True
        try:
            if option == LIGHT_OFF:
                if self._spaclient.get_light(self._light_num):
                    self._spaclient.set_light(self._light_num, False)
                self._current_option = LIGHT_OFF
                return

            colors = self._get_colors()
            target = next((c for c in colors if c[LED_COLOR_NAME] == option), None)
            if target is None:
                _LOGGER.warning("Unknown LED color option: %s", option)
                return
            cycles = target[LED_COLOR_CYCLES]

            delay_on = self._config_entry.options.get(CONF_LED_DELAY_ON, DEFAULT_LED_DELAY_ON) / 1000
            delay_off = self._config_entry.options.get(CONF_LED_DELAY_OFF, DEFAULT_LED_DELAY_OFF) / 1000
            delay_reset = self._config_entry.options.get(CONF_LED_DELAY_RESET, DEFAULT_LED_DELAY_RESET)

            # Reset the color cycle back to color 1: turn off and wait long enough
            # for the LED hardware to forget its current position.
            if self._spaclient.get_light(self._light_num):
                self._spaclient.set_light(self._light_num, False)
                await asyncio.sleep(delay_reset)

            # Advance the cycle: off (delay_off), then on (delay_on), repeated
            # `cycles` times. The light ends up ON after the last cycle,
            # displaying the selected color.
            for i in range(cycles):
                await asyncio.sleep(delay_off)
                self._spaclient.set_light(self._light_num, True)
                await asyncio.sleep(delay_on)
                if i < cycles - 1:
                    self._spaclient.set_light(self._light_num, False)

            self._current_option = option
        finally:
            self._cycling = False

    @property
    def available(self) -> bool:
        return self._spaclient.get_gateway_status()
