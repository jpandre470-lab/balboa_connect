"""Init file for Balboa Connect integration."""
import asyncio
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

# Import the device class from the component that you want to support
from .const import (
    _LOGGER,
    CONF_SYNC_TIME,
    CONF_FAULT_LOG_ENABLED,
    CONF_FAULT_LOG_INTERVAL,
    DATA_LISTENER,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_FAULT_LOG_INTERVAL,
    DOMAIN,
    ICONS,
    MIN_SCAN_INTERVAL,
    MIN_FAULT_LOG_INTERVAL,
    MAX_FAULT_LOG_INTERVAL,
    SPA,
    SPACLIENT_COMPONENTS,
)
from .spaclient import spaclient

# Task storage keys
DATA_READ_MSG_TASK = "read_msg_task"
DATA_SYNC_TIME_TASK = "sync_time_task"
DATA_FAULT_LOG_TASK = "fault_log_task"
from homeassistant.config_entries import SOURCE_IMPORT
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_SCAN_INTERVAL,
)
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.entity import Entity


CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_HOST): cv.string,
                vol.Required(CONF_NAME): cv.string,
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(cv.positive_int, vol.Clamp(min=MIN_SCAN_INTERVAL)),
                vol.Optional(CONF_SYNC_TIME, default=False): bool,
                vol.Optional(CONF_FAULT_LOG_ENABLED, default=False): bool,
                vol.Optional(CONF_FAULT_LOG_INTERVAL, default=DEFAULT_FAULT_LOG_INTERVAL): vol.All(cv.positive_int, vol.Clamp(min=MIN_FAULT_LOG_INTERVAL, max=MAX_FAULT_LOG_INTERVAL)),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass, base_config):
    """Configure the Balboa Connect component using flow only."""

    hass.data.setdefault(DOMAIN, {})

    if DOMAIN in base_config:
        for entry in base_config[DOMAIN]:
            hass.async_create_task(
                hass.config_entries.flow.async_init(
                    DOMAIN, context={"source": SOURCE_IMPORT}, data=entry
                )
            )
    return True


async def async_setup_entry(hass, config_entry):
    """Set up Balboa Connect from a config entry."""

    spa = spaclient(config_entry.data[CONF_HOST])
    hass.data[DOMAIN][config_entry.entry_id] = {
        SPA: spa, 
        DATA_LISTENER: [config_entry.add_update_listener(update_listener)],
        DATA_READ_MSG_TASK: None,
        DATA_SYNC_TIME_TASK: None,
        DATA_FAULT_LOG_TASK: None,
    }

    try:
        connected = await spa.validate_connection()

        if not connected:
            _LOGGER.error("Failed to connect to spa at %s", config_entry.data[CONF_HOST])
            raise ConfigEntryNotReady

        await spa.send_additional_information_request()
        await spa.send_configuration_request()
        await spa.send_fault_log_request()
        await spa.send_filter_cycles_request()
        await spa.send_gfci_test_request()
        await spa.send_information_request()
        await spa.send_preferences_request()
        await spa.send_module_identification_request()
        
    except Exception as e:
        _LOGGER.error("Error during spa initialization: %s", e)
        await spa.stop()
        raise ConfigEntryNotReady from e

    await update_listener(hass, config_entry)

    read_msg_task = hass.loop.create_task(spa.read_all_msg())
    
    hass.data[DOMAIN][config_entry.entry_id][DATA_READ_MSG_TASK] = read_msg_task

    await hass.config_entries.async_forward_entry_setups(config_entry, SPACLIENT_COMPONENTS)

    spa.print_variables()
    return True


async def async_unload_entry(hass, config_entry) -> bool:
    """Unload a config entry."""
    
    entry_data = hass.data[DOMAIN][config_entry.entry_id]
    
    spa = entry_data.get(SPA)
    if spa:
        await spa.stop()
    
    for task_key in [DATA_READ_MSG_TASK, DATA_SYNC_TIME_TASK, DATA_FAULT_LOG_TASK]:
        task = entry_data.get(task_key)
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
    
    for listener in entry_data.get(DATA_LISTENER, []):
        if callable(listener):
            listener()

    if unload_ok := await hass.config_entries.async_unload_platforms(config_entry, SPACLIENT_COMPONENTS):
        hass.data[DOMAIN].pop(config_entry.entry_id)
    
    _LOGGER.info("Balboa Connect unloaded successfully")
    return unload_ok


async def update_listener(hass, config_entry):
    """Handle options update."""

    entry_data = hass.data[DOMAIN][config_entry.entry_id]
    spa = entry_data.get(SPA)
    
    # Handle sync time task
    if config_entry.options.get(CONF_SYNC_TIME):
        existing_task = entry_data.get(DATA_SYNC_TIME_TASK)
        if existing_task and not existing_task.done():
            existing_task.cancel()
            try:
                await existing_task
            except asyncio.CancelledError:
                pass

        async def sync_time():
            while config_entry.options.get(CONF_SYNC_TIME) and not spa._stop_flag:
                try:
                    await spa.set_current_time()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    _LOGGER.error("Error syncing time: %s", e)
                await asyncio.sleep(86400)

        sync_task = hass.loop.create_task(sync_time())
        entry_data[DATA_SYNC_TIME_TASK] = sync_task
    else:
        existing_task = entry_data.get(DATA_SYNC_TIME_TASK)
        if existing_task and not existing_task.done():
            existing_task.cancel()
            try:
                await existing_task
            except asyncio.CancelledError:
                pass
        entry_data[DATA_SYNC_TIME_TASK] = None

    # Handle fault log task
    if config_entry.options.get(CONF_FAULT_LOG_ENABLED, False):
        fault_log_interval = config_entry.options.get(CONF_FAULT_LOG_INTERVAL, DEFAULT_FAULT_LOG_INTERVAL)
        existing_task = entry_data.get(DATA_FAULT_LOG_TASK)
        if existing_task and not existing_task.done():
            existing_task.cancel()
            try:
                await existing_task
            except asyncio.CancelledError:
                pass

        async def fault_log_task():
            while config_entry.options.get(CONF_FAULT_LOG_ENABLED, False) and not spa._stop_flag:
                try:
                    await spa.send_fault_log_request()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    _LOGGER.error("Error requesting fault log: %s", e)
                await asyncio.sleep(fault_log_interval * 3600)

        fl_task = hass.loop.create_task(fault_log_task())
        entry_data[DATA_FAULT_LOG_TASK] = fl_task
    else:
        existing_task = entry_data.get(DATA_FAULT_LOG_TASK)
        if existing_task and not existing_task.done():
            existing_task.cancel()
            try:
                await existing_task
            except asyncio.CancelledError:
                pass
        entry_data[DATA_FAULT_LOG_TASK] = None


class SpaClientDevice(Entity):
    """Representation of a Balboa Connect device."""

    def __init__(self, spaclient, config_entry):
        """Initialize the Balboa Connect device."""
        self._device_name = config_entry.data[CONF_NAME]
        self._spaclient = spaclient

    async def async_added_to_hass(self):
        """Register state update callback."""

    @property
    def should_poll(self) -> bool:
        """Home Assistant will poll an entity when the should_poll property returns True."""
        return True

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self._spaclient.get_macaddr().replace(':', '')}#balboa_connect"

    @property
    def device_info(self):
        """Return the device information for this entity."""
        return {
            "identifiers": {(DOMAIN, self._spaclient.get_macaddr().replace(':', ''))},
            "model": self._spaclient.get_model_name(),
            "manufacturer": "Balboa Water Group",
            "name": self._device_name,
            "sw_version": self._spaclient.get_ssid(),
        }
