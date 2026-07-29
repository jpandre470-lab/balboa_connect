"""Config flow for Balboa Connect integration."""
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

# Import the device class from the component that you want to support
from .const import (
    _LOGGER,
    CONF_SYNC_TIME,
    CONF_KEEPALIVE_ENABLED,
    CONF_KEEPALIVE_INTERVAL,
    CONF_KEEPALIVE_FRAME_TYPE,
    CONF_SOCKET_TIMEOUT,
    CONF_LED_COLORS,
    CONF_LED_DELAY_OFF,
    CONF_LED_DELAY_ON,
    CONF_LED_DELAY_RESET,
    CONF_LIGHT_MODE,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_KEEPALIVE_ENABLED,
    DEFAULT_KEEPALIVE_INTERVAL,
    DEFAULT_KEEPALIVE_FRAME_TYPE,
    DEFAULT_SOCKET_TIMEOUT,
    DEFAULT_LED_COLORS,
    DEFAULT_LED_DELAY_OFF,
    DEFAULT_LED_DELAY_ON,
    DEFAULT_LED_DELAY_RESET,
    DEFAULT_LIGHT_MODE,
    DOMAIN,
    KEEPALIVE_FRAME_TYPES,
    LED_COLOR_CYCLES,
    LED_COLOR_NAME,
    LED_COLOR_RGB,
    LIGHT_MODE_COLOR,
    LIGHT_MODE_SWITCH,
    MIN_SCAN_INTERVAL,
    MIN_KEEPALIVE_INTERVAL,
    MAX_KEEPALIVE_INTERVAL,
    MIN_SOCKET_TIMEOUT,
    MAX_SOCKET_TIMEOUT,
    MIN_LED_DELAY_MS,
    MAX_LED_DELAY_MS,
    MIN_LED_DELAY_RESET,
    MAX_LED_DELAY_RESET,
)
from .spaclient import spaclient
from homeassistant import config_entries, core, exceptions
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_SCAN_INTERVAL,
)
from homeassistant.core import callback


DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_NAME, default="Balboa Connect"): str,
    }
)


@callback
def configured_instances(hass):
    """Return a set of configured Balboa Connect instances."""

    return {entry.title for entry in hass.config_entries.async_entries(DOMAIN)}


class SpaClientConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Balboa Connect."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    async def async_step_import(self, import_config):
        """Import a config entry from configuration.yaml."""
        return await self.async_step_user(import_config)

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input:
            try:
                await validate_input(self.hass, user_input)
                return self.async_create_entry(title="", data=user_input)
            except AlreadyConfigured:
                return self.async_abort(reason="already_configured")
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler()


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle a option flow for Balboa Connect."""

    def __init__(self):
        """Initialize the options flow state."""
        self._new_options = {}
        self._led_colors = []
        self._edit_index = None

    async def async_step_init(self, user_input=None):
        """Handle options flow - step 1: general settings + light mode choice."""
        if user_input is not None:
            self._new_options = dict(user_input)
            self._led_colors = list(
                self.config_entry.options.get(CONF_LED_COLORS, DEFAULT_LED_COLORS)
            )
            if user_input.get(CONF_LIGHT_MODE) == LIGHT_MODE_COLOR:
                return await self.async_step_led_palette()
            # Switch mode: no LED palette to store
            self._new_options.pop(CONF_LED_COLORS, None)
            return self.async_create_entry(title="", data=self._new_options)

        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=self.config_entry.options.get(
                        CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                    ),
                ): vol.All(cv.positive_int, vol.Clamp(min=MIN_SCAN_INTERVAL)),
                vol.Optional(
                    CONF_SYNC_TIME,
                    default=self.config_entry.options.get(CONF_SYNC_TIME, False),
                ): bool,
                vol.Optional(
                    CONF_KEEPALIVE_ENABLED,
                    default=self.config_entry.options.get(
                        CONF_KEEPALIVE_ENABLED, DEFAULT_KEEPALIVE_ENABLED
                    ),
                ): bool,
                vol.Optional(
                    CONF_KEEPALIVE_INTERVAL,
                    default=self.config_entry.options.get(
                        CONF_KEEPALIVE_INTERVAL, DEFAULT_KEEPALIVE_INTERVAL
                    ),
                ): vol.All(
                    cv.positive_int,
                    vol.Clamp(min=MIN_KEEPALIVE_INTERVAL, max=MAX_KEEPALIVE_INTERVAL),
                ),
                vol.Optional(
                    CONF_KEEPALIVE_FRAME_TYPE,
                    default=self.config_entry.options.get(
                        CONF_KEEPALIVE_FRAME_TYPE, DEFAULT_KEEPALIVE_FRAME_TYPE
                    ),
                ): vol.In(KEEPALIVE_FRAME_TYPES),
                vol.Optional(
                    CONF_SOCKET_TIMEOUT,
                    default=self.config_entry.options.get(
                        CONF_SOCKET_TIMEOUT, DEFAULT_SOCKET_TIMEOUT
                    ),
                ): vol.All(
                    cv.positive_int,
                    vol.Clamp(min=MIN_SOCKET_TIMEOUT, max=MAX_SOCKET_TIMEOUT),
                ),
                vol.Optional(
                    CONF_LIGHT_MODE,
                    default=self.config_entry.options.get(
                        CONF_LIGHT_MODE, DEFAULT_LIGHT_MODE
                    ),
                ): vol.In(
                    {
                        LIGHT_MODE_SWITCH: "Simple switch (on/off)",
                        LIGHT_MODE_COLOR: "Multi-color LED (palette)",
                    }
                ),
            }
        )
        return self.async_show_form(step_id="init", data_schema=data_schema)

    async def async_step_led_palette(self, user_input=None):
        """Step 2 (color mode only): LED palette management."""
        if user_input is not None:
            self._new_options[CONF_LED_DELAY_ON] = user_input.get(
                CONF_LED_DELAY_ON, DEFAULT_LED_DELAY_ON
            )
            self._new_options[CONF_LED_DELAY_OFF] = user_input.get(
                CONF_LED_DELAY_OFF, DEFAULT_LED_DELAY_OFF
            )
            self._new_options[CONF_LED_DELAY_RESET] = user_input.get(
                CONF_LED_DELAY_RESET, DEFAULT_LED_DELAY_RESET
            )
            action = user_input.get("action", "save")
            if action == "save":
                self._new_options[CONF_LED_COLORS] = self._led_colors
                return self.async_create_entry(title="", data=self._new_options)
            if action == "add":
                self._edit_index = None
                return await self.async_step_led_edit()
            if action == "reset":
                self._led_colors = list(DEFAULT_LED_COLORS)
                return await self.async_step_led_palette()
            if action.startswith("delete_"):
                self._led_colors.pop(int(action.split("_")[1]))
                return await self.async_step_led_palette()
            if action.startswith("edit_"):
                self._edit_index = int(action.split("_")[1])
                return await self.async_step_led_edit()

        opts = self.config_entry.options
        lines = [
            f"{i + 1}. {c[LED_COLOR_NAME]} \u2014 {c[LED_COLOR_CYCLES]} cycle(s)"
            f" \u2014 RGB({','.join(str(v) for v in c[LED_COLOR_RGB])})"
            for i, c in enumerate(self._led_colors)
        ]
        palette_text = "\n".join(lines) or "(empty)"

        choices = {
            "save": "Save",
            "add": "Add a color",
            "reset": "Reset to default palette",
        }
        for i, c in enumerate(self._led_colors):
            choices[f"edit_{i}"] = f"Edit: {c[LED_COLOR_NAME]}"
            choices[f"delete_{i}"] = f"Delete: {c[LED_COLOR_NAME]}"

        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_LED_DELAY_ON,
                    default=opts.get(CONF_LED_DELAY_ON, DEFAULT_LED_DELAY_ON),
                ): vol.All(vol.Coerce(int), vol.Range(min=MIN_LED_DELAY_MS, max=MAX_LED_DELAY_MS)),
                vol.Optional(
                    CONF_LED_DELAY_OFF,
                    default=opts.get(CONF_LED_DELAY_OFF, DEFAULT_LED_DELAY_OFF),
                ): vol.All(vol.Coerce(int), vol.Range(min=MIN_LED_DELAY_MS, max=MAX_LED_DELAY_MS)),
                vol.Optional(
                    CONF_LED_DELAY_RESET,
                    default=opts.get(CONF_LED_DELAY_RESET, DEFAULT_LED_DELAY_RESET),
                ): vol.All(vol.Coerce(int), vol.Range(min=MIN_LED_DELAY_RESET, max=MAX_LED_DELAY_RESET)),
                vol.Required("action", default="save"): vol.In(choices),
            }
        )
        return self.async_show_form(
            step_id="led_palette",
            data_schema=data_schema,
            description_placeholders={"palette": palette_text},
        )

    async def async_step_led_edit(self, user_input=None):
        """Step 3 (color mode only): add or edit a single LED color."""
        errors = {}
        if user_input is not None:
            try:
                parts = [int(x.strip()) for x in user_input["rgb"].split(",")]
                if len(parts) != 3 or not all(0 <= v <= 255 for v in parts):
                    raise ValueError
            except (ValueError, AttributeError):
                errors["rgb"] = "invalid_rgb"
            else:
                entry = {
                    LED_COLOR_NAME: user_input["name"].strip(),
                    LED_COLOR_CYCLES: user_input["cycles"],
                    LED_COLOR_RGB: parts,
                }
                if self._edit_index is None:
                    self._led_colors.append(entry)
                else:
                    self._led_colors[self._edit_index] = entry
                return await self.async_step_led_palette()

        if self._edit_index is not None:
            existing = self._led_colors[self._edit_index]
            default_name = existing[LED_COLOR_NAME]
            default_cycles = existing[LED_COLOR_CYCLES]
            default_rgb = "{},{},{}".format(*existing[LED_COLOR_RGB])
        else:
            default_name, default_cycles, default_rgb = "", 1, "255,255,255"

        data_schema = vol.Schema(
            {
                vol.Required("name", default=default_name): str,
                vol.Required("cycles", default=default_cycles): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=99)
                ),
                vol.Required("rgb", default=default_rgb): str,
            }
        )
        return self.async_show_form(
            step_id="led_edit", data_schema=data_schema, errors=errors
        )


async def validate_input(hass, data):
    """Validate the user input allows us to connect."""

    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.data[CONF_HOST] == data[CONF_HOST]:
            raise AlreadyConfigured

    spa = spaclient(data[CONF_HOST])

    connected = await spa.validate_connection()  # To switch to development mode, comment out this line

    if not connected:  # To switch to development mode, comment out this line
        raise CannotConnect  # To switch to development mode, comment out this line


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class AlreadyConfigured(exceptions.HomeAssistantError):
    """Error to indicate this device is already configured."""
