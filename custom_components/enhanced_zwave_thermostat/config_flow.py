"""Config flow for Enhanced Z-Wave Thermostat integration."""
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    CONF_SELECTED_CLIMATE_ENTITY,
    CONF_SAFETY_MIN_TEMP,
    CONF_SAFETY_MAX_TEMP,
    CONF_HOME_TEMP,
    CONF_AWAY_TEMP,
    DEFAULT_SAFETY_MIN_TEMP,
    DEFAULT_SAFETY_MAX_TEMP,
    DEFAULT_HOME_TEMP,
    DEFAULT_AWAY_TEMP,
)

_LOGGER = logging.getLogger(__name__)


class EnhancedZWaveThermostatConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Enhanced Z-Wave Thermostat."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step."""
        errors = {}
        
        if user_input is not None:
            try:
                # Basic validation
                min_temp = user_input.get(CONF_SAFETY_MIN_TEMP, DEFAULT_SAFETY_MIN_TEMP)
                max_temp = user_input.get(CONF_SAFETY_MAX_TEMP, DEFAULT_SAFETY_MAX_TEMP)
                
                if min_temp >= max_temp:
                    errors["base"] = "invalid_temp_range"
                else:
                    # Allow multiple instances - create unique title
                    entity_id = user_input.get(CONF_SELECTED_CLIMATE_ENTITY, "").strip()
                    if entity_id:
                        title = f"Enhanced Z-Wave Thermostat ({entity_id})"
                    else:
                        # If no entity specified, create a generic instance
                        existing_count = len(self._async_current_entries())
                        title = f"Enhanced Z-Wave Thermostat ({existing_count + 1})"
                    
                    return self.async_create_entry(
                        title=title,
                        data=user_input
                    )
            except Exception as err:
                _LOGGER.error("Error during configuration: %s", err, exc_info=True)
                errors["base"] = "cannot_connect"

        # Simple form
        data_schema = vol.Schema({
            vol.Optional(CONF_SELECTED_CLIMATE_ENTITY, default=""): str,
            vol.Optional(CONF_SAFETY_MIN_TEMP, default=DEFAULT_SAFETY_MIN_TEMP): 
                vol.All(vol.Coerce(int), vol.Range(min=32, max=80)),
            vol.Optional(CONF_SAFETY_MAX_TEMP, default=DEFAULT_SAFETY_MAX_TEMP):
                vol.All(vol.Coerce(int), vol.Range(min=60, max=100)),
            vol.Optional(CONF_HOME_TEMP, default=DEFAULT_HOME_TEMP):
                vol.All(vol.Coerce(int), vol.Range(min=50, max=85)),
            vol.Optional(CONF_AWAY_TEMP, default=DEFAULT_AWAY_TEMP):
                vol.All(vol.Coerce(int), vol.Range(min=50, max=85)),
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return EnhancedZWaveThermostatOptionsFlow(config_entry)


class EnhancedZWaveThermostatOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Enhanced Z-Wave Thermostat."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data_schema = vol.Schema({
            vol.Optional(
                CONF_SAFETY_MIN_TEMP,
                default=self.config_entry.options.get(
                    CONF_SAFETY_MIN_TEMP, DEFAULT_SAFETY_MIN_TEMP
                )
            ): vol.All(vol.Coerce(int), vol.Range(min=32, max=80)),
            vol.Optional(
                CONF_SAFETY_MAX_TEMP,
                default=self.config_entry.options.get(
                    CONF_SAFETY_MAX_TEMP, DEFAULT_SAFETY_MAX_TEMP
                )
            ): vol.All(vol.Coerce(int), vol.Range(min=60, max=100)),
        })

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
        )