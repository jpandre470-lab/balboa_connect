"""Config flow for Balboa Connect integration."""
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from .const import (
    _LOGGER,
    CONF_SYNC_TIME,
    CONF_SYNC_TIME_INTERVAL,
    CONF_SOCKET_TIMEOUT,
    CONF_FAULT_LOG_ENABLED,
    CONF_FAULT_LOG_INTERVAL,
    DEFAULT_SYNC_TIME_INTERVAL,
    DEFAULT_SOCKET_TIMEOUT,
    DEFAULT_FAULT_LOG_INTERVAL,
    DOMAIN,
    MIN_SYNC_TIME_INTERVAL,
    MAX_SYNC_TIME_INTERVAL,
    MIN_SOCKET_TIMEOUT,
    MAX_SOCKET_TIMEOUT,
    MIN_FAULT_LOG_INTERVAL,
    MAX_FAULT_LOG_INTERVAL,
)
from .spaclient import spaclient
from homeassistant import config_entries, exceptions
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
)
from homeassistant.core import callback


DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_NAME, default="Balboa Spa"): str,
    }
)


@callback
def configured_instances(hass):
    """Return a set of configured Balboa Connect instances."""
    return {entry.title for entry in hass.config_entries.async_entries(DOMAIN)}


class BalboaConnectConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
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

    async def async_step_init(self, user_input=None):
        """Handle options flow."""
        if user_input:
            return self.async_create_entry(title="", data=user_input)

        SYNC_INTERVAL_OPTIONS = [1, 2, 3, 4, 6, 8, 12, 24]
        FAULT_LOG_INTERVAL_OPTIONS = [1, 2, 3, 4, 6, 8, 12, 24]

        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_SYNC_TIME,
                    default=True,
                    description="Enable automatic time synchronization with Home Assistant"
                ): bool,
                vol.Optional(
                    CONF_SYNC_TIME_INTERVAL,
                    default=self.config_entry.options.get(
                        CONF_SYNC_TIME_INTERVAL, DEFAULT_SYNC_TIME_INTERVAL
                    ),
                    description=f"Sync interval in hours (min: {MIN_SYNC_TIME_INTERVAL}, max: {MAX_SYNC_TIME_INTERVAL})"
                ): vol.In(SYNC_INTERVAL_OPTIONS),
                vol.Optional(
                    CONF_SOCKET_TIMEOUT,
                    default=self.config_entry.options.get(
                        CONF_SOCKET_TIMEOUT, DEFAULT_SOCKET_TIMEOUT
                    ),
                    description=f"Socket timeout in seconds (min: {MIN_SOCKET_TIMEOUT}, max: {MAX_SOCKET_TIMEOUT})"
                ): vol.All(cv.positive_int, vol.Clamp(min=MIN_SOCKET_TIMEOUT, max=MAX_SOCKET_TIMEOUT)),
                vol.Optional(
                    CONF_FAULT_LOG_ENABLED,
                    default=False,
                    description="Enable periodic fault log requests"
                ): bool,
                vol.Optional(
                    CONF_FAULT_LOG_INTERVAL,
                    default=self.config_entry.options.get(
                        CONF_FAULT_LOG_INTERVAL, DEFAULT_FAULT_LOG_INTERVAL
                    ),
                    description=f"Fault log interval in hours (min: {MIN_FAULT_LOG_INTERVAL}, max: {MAX_FAULT_LOG_INTERVAL})"
                ): vol.In(FAULT_LOG_INTERVAL_OPTIONS),
            }
        )
        return self.async_show_form(step_id="init", data_schema=data_schema)


async def validate_input(hass, data):
    """Validate the user input allows us to connect."""
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.data[CONF_HOST] == data[CONF_HOST]:
            raise AlreadyConfigured

    spa = spaclient(data[CONF_HOST])
    connected = await spa.validate_connection()
    if not connected:
        raise CannotConnect


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class AlreadyConfigured(exceptions.HomeAssistantError):
    """Error to indicate this device is already configured."""
