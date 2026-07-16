"""Support for Balboa Connect climate device."""
# Import the device class from the component that you want to support
from . import SpaClientDevice
from .const import _LOGGER, DOMAIN, ICONS, SPA
from datetime import timedelta
from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature, HVACAction, HVACMode
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.util.unit_conversion import TemperatureConverter

SCAN_INTERVAL = timedelta(seconds=1)

SUPPORT_HVAC = [HVACMode.HEAT, HVACMode.OFF, HVACMode.AUTO]

# Mapping between spa heat modes and HVAC modes.
# This mirrors the official Home Assistant Core Balboa integration
# (homeassistant/components/balboa/climate.py), with one deliberate
# difference: AUTO is included in hvac_modes so the thermostat card
# correctly reflects the state when the spa enters "Ready in Rest" on its
# own, instead of only being visible through get_heat_mode()/select.py.
# - Ready -> HEAT (actively heating to reach the set point)
# - Rest -> OFF (heating restricted to filter cycles only; not a real "off",
#   but closer to it semantically than COOL, which implies active cooling
#   a spa can never actually do)
# - Ready in Rest -> AUTO. This state is entered automatically by the spa
#   when a pump starts while in Rest mode; there is no direct command to
#   request it, so it is deliberately left out of HVAC_TO_HEAT_MODE.
#   Selecting "Auto" from the thermostat card is therefore a silent no-op
#   (see async_set_hvac_mode) - it's included in hvac_modes for display,
#   not as something you can actively request.
HEAT_MODE_TO_HVAC = {
    "Ready": HVACMode.HEAT,
    "Rest": HVACMode.OFF,
    "Ready in Rest": HVACMode.AUTO,
}

HVAC_TO_HEAT_MODE = {
    HVACMode.HEAT: "Ready",
    HVACMode.OFF: "Rest",
}

# Presets mirror the spa's own heat mode names directly on the thermostat
# card. "Ready in Rest" is excluded from the settable list for the same
# reason as hvac_modes/select.py: there is no direct command to force it,
# it only occurs automatically - but preset_mode can still report it.
PRESET_MODES = ["Ready", "Rest"]


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Setup the Balboa Connect climate device."""

    spaclient = hass.data[DOMAIN][config_entry.entry_id][SPA]
    entities = []

    entities.append(SpaThermostat(spaclient, config_entry))

    async_add_entities(entities, True)


class SpaThermostat(SpaClientDevice, ClimateEntity):
    """Representation of a climate device."""
    _enable_turn_on_off_backwards_compatibility = False

    def __init__(self, spaclient, config_entry):
        """Initialize the device."""
        super().__init__(spaclient, config_entry)
        self._spaclient = spaclient
        self._icon = ICONS.get('Spa Thermostat')

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return f"{self._spaclient.get_macaddr().replace(':', '')}#spa_thermostat"

    @property
    def name(self):
        """Return the name of the device."""
        return 'Spa Thermostat'

    @property
    def icon(self):
        """Return the icon of the device."""
        return self._icon

    @property
    def hvac_mode(self):
        """Return current HVAC mode based on heat mode.

        Ready = HEAT (actively heating to reach the set point)
        Rest = OFF (heating restricted to filter cycles only)
        Ready in Rest = AUTO (visible in the thermostat card, but not
        selectable - see async_set_hvac_mode)
        """
        heat_mode = self._spaclient.get_heat_mode()
        return HEAT_MODE_TO_HVAC.get(heat_mode, HVACMode.OFF)

    @property
    def hvac_action(self):
        """Return the current HVAC action.
        
        heating == 0: Off
        heating == 1: Heating
        heating == 2: Heat Waiting (preparing for heat)
        """
        if self._spaclient.get_standby_mode():
            return HVACAction.OFF
        heating = self._spaclient.get_heating()
        if heating == 1:
            return HVACAction.HEATING
        if heating == 2:
            return HVACAction.IDLE  # Heat Waiting / preparing for heat
        return HVACAction.IDLE

    @property
    def hvac_modes(self):
        """Return available HVAC modes."""
        return SUPPORT_HVAC

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE

    @property
    def preset_modes(self):
        """Return available presets (spa heat mode names, directly on the thermostat card)."""
        return PRESET_MODES

    @property
    def preset_mode(self):
        """Return the current preset (spa heat mode: Ready, Rest, or Ready in Rest)."""
        return self._spaclient.get_heat_mode()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the spa heat mode directly via its own names."""
        self._spaclient.set_heat_mode(preset_mode)

    @property
    def current_temperature(self):
        """Return the current temperature."""
        if self._spaclient.get_current_temp() != None:
            if self.hass.config.units.temperature_unit == UnitOfTemperature.CELSIUS and self._spaclient.temp_scale == "Fahrenheit":
                return round(TemperatureConverter.convert(self._spaclient.get_current_temp(), UnitOfTemperature.FAHRENHEIT, UnitOfTemperature.CELSIUS) * 2) / 2
            if self.hass.config.units.temperature_unit == UnitOfTemperature.CELSIUS and self._spaclient.temp_scale == "Celsius":
                return self._spaclient.get_current_temp() / 2
            if self.hass.config.units.temperature_unit == UnitOfTemperature.FAHRENHEIT and self._spaclient.temp_scale == "Celsius":
                return round(TemperatureConverter.convert(self._spaclient.get_current_temp() / 2, UnitOfTemperature.CELSIUS, UnitOfTemperature.FAHRENHEIT) * 2) / 2
            return self._spaclient.get_current_temp()
        return None

    @property
    def target_temperature(self):
        """Return the target temperature."""
        if self.hass.config.units.temperature_unit == UnitOfTemperature.CELSIUS and self._spaclient.temp_scale == "Fahrenheit":
            return round(TemperatureConverter.convert(self._spaclient.get_set_temp(), UnitOfTemperature.FAHRENHEIT, UnitOfTemperature.CELSIUS) * 2) / 2
        if self.hass.config.units.temperature_unit == UnitOfTemperature.CELSIUS and self._spaclient.temp_scale == "Celsius":
            return self._spaclient.get_set_temp() / 2
        if self.hass.config.units.temperature_unit == UnitOfTemperature.FAHRENHEIT and self._spaclient.temp_scale == "Celsius":
            return round(TemperatureConverter.convert(self._spaclient.get_set_temp() / 2, UnitOfTemperature.CELSIUS, UnitOfTemperature.FAHRENHEIT) * 2) / 2
        return self._spaclient.get_set_temp()

    async def async_set_temperature(self, **kwargs):
        temperature = kwargs[ATTR_TEMPERATURE]
        if self.hass.config.units.temperature_unit == UnitOfTemperature.CELSIUS and self._spaclient.temp_scale == "Fahrenheit":
            temperature = round(TemperatureConverter.convert(temperature, UnitOfTemperature.CELSIUS, UnitOfTemperature.FAHRENHEIT))
        if self.hass.config.units.temperature_unit == UnitOfTemperature.CELSIUS and self._spaclient.temp_scale == "Celsius":
            temperature = temperature * 2
        if self.hass.config.units.temperature_unit == UnitOfTemperature.FAHRENHEIT and self._spaclient.temp_scale == "Celsius":
            temperature = round(TemperatureConverter.convert(temperature, UnitOfTemperature.FAHRENHEIT, UnitOfTemperature.CELSIUS) * 2)
        await self._spaclient.set_temperature(temperature)

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target HVAC mode via heat mode.

        HEAT = Ready (actively heating to reach the set point)
        OFF = Rest (heating restricted to filter cycles only)
        AUTO = Ready in Rest, included in hvac_modes for display only. It
        cannot be requested directly (see HVAC_TO_HEAT_MODE) - it only
        occurs automatically, so selecting it here is a no-op.
        """
        if hvac_mode not in HVAC_TO_HEAT_MODE:
            if hvac_mode == HVACMode.AUTO:
                _LOGGER.info(
                    "HVAC mode 'auto' (Ready in Rest) cannot be set directly; "
                    "it only occurs automatically when a pump starts while in Rest mode."
                )
            return
        heat_mode = HVAC_TO_HEAT_MODE[hvac_mode]
        self._spaclient.set_heat_mode(heat_mode)

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        if self._spaclient.get_temp_range() == "High":
            if self.hass.config.units.temperature_unit == UnitOfTemperature.CELSIUS:
                return round(TemperatureConverter.convert(self._spaclient.get_high_range_min(), UnitOfTemperature.FAHRENHEIT, UnitOfTemperature.CELSIUS) * 2) / 2
            return TemperatureConverter.convert(self._spaclient.get_high_range_min(), UnitOfTemperature.FAHRENHEIT, self.temperature_unit)
        if self.hass.config.units.temperature_unit == UnitOfTemperature.CELSIUS:
            return round(TemperatureConverter.convert(self._spaclient.get_low_range_min(), UnitOfTemperature.FAHRENHEIT, UnitOfTemperature.CELSIUS) * 2) / 2
        return TemperatureConverter.convert(self._spaclient.get_low_range_min(), UnitOfTemperature.FAHRENHEIT, self.temperature_unit)

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        if self._spaclient.get_temp_range() == "High":
            if self.hass.config.units.temperature_unit == UnitOfTemperature.CELSIUS:
                return round(TemperatureConverter.convert(self._spaclient.get_high_range_max(), UnitOfTemperature.FAHRENHEIT, UnitOfTemperature.CELSIUS) * 2) / 2
            return TemperatureConverter.convert(self._spaclient.get_high_range_max(), UnitOfTemperature.FAHRENHEIT, self.temperature_unit)
        if self.hass.config.units.temperature_unit == UnitOfTemperature.CELSIUS:
            return round(TemperatureConverter.convert(self._spaclient.get_low_range_max(), UnitOfTemperature.FAHRENHEIT, UnitOfTemperature.CELSIUS) * 2) / 2
        return TemperatureConverter.convert(self._spaclient.get_low_range_max(), UnitOfTemperature.FAHRENHEIT, self.temperature_unit)

    @property
    def temperature_unit(self):
        """Return the unit of measurement used by the platform."""
        if self.hass.config.units.temperature_unit == UnitOfTemperature.CELSIUS:
            return UnitOfTemperature.CELSIUS
        return UnitOfTemperature.FAHRENHEIT

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        attrs = {}
        attrs["Heating State"] = self._spaclient.get_heating_state()
        attrs["Standby Mode"] = "On" if self._spaclient.get_standby_mode() else "Off"
        attrs["Temperature Range"] = self._spaclient.get_temp_range()
        attrs["Temperature Scale"] = self._spaclient.get_temp_scale()
        return attrs

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._spaclient.get_gateway_status()
