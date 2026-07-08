"""Init file for Balboa Connect integration."""
import asyncio
import types
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

# Import the device class from the component that you want to support
from .const import (
    CONF_SOCKET_TIMEOUT,
    DEFAULT_SOCKET_TIMEOUT,
    CONF_KEEPALIVE_ENABLED,
    CONF_KEEPALIVE_INTERVAL,
    CONF_KEEPALIVE_FRAME_TYPE,
    DEFAULT_KEEPALIVE_ENABLED,
    DEFAULT_KEEPALIVE_INTERVAL,
    DEFAULT_KEEPALIVE_FRAME_TYPE,
    _LOGGER,
    CONF_SYNC_TIME,
    DATA_LISTENER,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    ICONS,
    MIN_SCAN_INTERVAL,
    SPA,
    SPACLIENT_COMPONENTS,
)
from .spaclient import spaclient

# Task storage keys
DATA_KEEP_ALIVE_TASK = "keep_alive_task"
DATA_READ_MSG_TASK = "read_msg_task"
DATA_SYNC_TIME_TASK = "sync_time_task"
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

    keepalive_enabled = config_entry.options.get(CONF_KEEPALIVE_ENABLED, DEFAULT_KEEPALIVE_ENABLED)
    keepalive_interval = config_entry.options.get(CONF_KEEPALIVE_INTERVAL, DEFAULT_KEEPALIVE_INTERVAL)
    keepalive_frame_type = config_entry.options.get(CONF_KEEPALIVE_FRAME_TYPE, DEFAULT_KEEPALIVE_FRAME_TYPE)
    spa = spaclient(
        config_entry.data[CONF_HOST],
        keepalive_enabled,
        keepalive_interval,
        keepalive_frame_type=keepalive_frame_type,
    )

    # Attach logging wrappers to spa send functions so we can capture raw frames without editing spaclient.py
    try:
        orig_send_message = spa.send_message
        def _log_and_send(self, type, payload):
            try:
                length = 5 + len(payload)
                checksum = None
                if hasattr(self, 'compute_checksum'):
                    checksum = self.compute_checksum(length - 1, bytes([length]) + type + payload)
                prefix = b'\x7e'
                if checksum is not None:
                    message = prefix + bytes([length]) + type + payload + bytes([checksum]) + prefix
                else:
                    message = prefix + bytes([length]) + type + payload + prefix
                _LOGGER.debug("Outbound message (encapsulated): %s", message.hex())
            except Exception as e:
                _LOGGER.debug("Failed building message hex: %s", e)
            # orig_send_message is a bound method; call it with the original signature
            return orig_send_message(type, payload)
        spa.send_message = types.MethodType(_log_and_send, spa)
    except Exception:
        _LOGGER.debug("Could not attach send_message wrapper")

    try:
        orig_send_async = getattr(spa, '_send_message_async', None)
        if orig_send_async:
            async def _log_and_send_async(self, type, payload):
                try:
                    length = 5 + len(payload)
                    checksum = None
                    if hasattr(self, 'compute_checksum'):
                        checksum = self.compute_checksum(length - 1, bytes([length]) + type + payload)
                    prefix = b'\x7e'
                    if checksum is not None:
                        message = prefix + bytes([length]) + type + payload + bytes([checksum]) + prefix
                    else:
                        message = prefix + bytes([length]) + type + payload + prefix
                    _LOGGER.debug("Outbound async message (encapsulated): %s", message.hex())
                except Exception as e:
                    _LOGGER.debug("Failed building async message hex: %s", e)
                return await orig_send_async(type, payload)
            spa._send_message_async = types.MethodType(_log_and_send_async, spa)
    except Exception:
        _LOGGER.debug("Could not attach _send_message_async wrapper")

    hass.data[DOMAIN][config_entry.entry_id] = {
        SPA: spa, 
        DATA_LISTENER: [config_entry.add_update_listener(update_listener)],
        DATA_KEEP_ALIVE_TASK: None,
        DATA_READ_MSG_TASK: None,
        DATA_SYNC_TIME_TASK: None,
    }

    try:
        connected = await spa.validate_connection()     #To switch to development mode, comment out this line

        if not connected:                               #To switch to development mode, comment out this line
            _LOGGER.error("Failed to connect to spa at %s", config_entry.data[CONF_HOST])
            raise ConfigEntryNotReady                   #To switch to development mode, comment out this line

        await spa.send_additional_information_request() #To switch to development mode, comment out this line
        await spa.send_configuration_request()          #To switch to development mode, comment out this line
        await spa.send_fault_log_request()              #To switch to development mode, comment out this line
        await spa.send_filter_cycles_request()          #To switch to development mode, comment out this line
        await spa.send_gfci_test_request()              #To switch to development mode, comment out this line
        await spa.send_information_request()            #To switch to development mode, comment out this line
        await spa.send_preferences_request()            #To switch to development mode, comment out this line
        await spa.send_module_identification_request()  #To switch to development mode, comment out this line
        
    except Exception as e:
        _LOGGER.error("Error during spa initialization: %s", e)
        await spa.stop()
        raise ConfigEntryNotReady from e

    await update_listener(hass, config_entry)

    # Create and store task references so we can cancel them on unload
    keep_alive_task = hass.loop.create_task(spa.keep_alive_call())
    read_msg_task = hass.loop.create_task(spa.read_all_msg())
    
    hass.data[DOMAIN][config_entry.entry_id][DATA_KEEP_ALIVE_TASK] = keep_alive_task
    hass.data[DOMAIN][config_entry.entry_id][DATA_READ_MSG_TASK] = read_msg_task

    await hass.config_entries.async_forward_entry_setups(config_entry, SPACLIENT_COMPONENTS)

    spa.print_variables()
    return True


async def async_unload_entry(hass, config_entry) -> bool:
    """Unload a config entry."""
    
    entry_data = hass.data[DOMAIN][config_entry.entry_id]
    
    # Stop the spa client first (sets stop flag)
    spa = entry_data.get(SPA)
    if spa:
        await spa.stop()
    
    # Cancel all running tasks
    for task_key in [DATA_KEEP_ALIVE_TASK, DATA_READ_MSG_TASK, DATA_SYNC_TIME_TASK]:
        task = entry_data.get(task_key)
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
    
    # Remove update listeners
    for listener in entry_data.get(DATA_LISTENER, []):
        if callable(listener):
            listener()

    if unload_ok := await hass.config_entries.async_unload_platforms(config_entry, SPACLIENT_COMPONENTS):
        hass.data[DOMAIN].pop(config_entry.entry_id)
    
    _LOGGER.info("Balboa Connect unloaded successfully")
    return unload_ok


async def update_listener(hass, config_entry):
    """Handle options update."""

    if config_entry.options.get(CONF_SYNC_TIME):
        spa = hass.data[DOMAIN][config_entry.entry_id][SPA]
        entry_data = hass.data[DOMAIN][config_entry.entry_id]
        
        # Cancel existing sync time task if any
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
