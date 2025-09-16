"""Config flow for Enhanced Z-Wave Thermostat integration."""
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    DOMAIN,
    CONF_THERMOSTATS,
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
            # Validate the input
            try:
                # Check if integration is already configured
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_configured()
                
                return self.async_create_entry(
                    title="Enhanced Z-Wave Thermostat",
                    data=user_input
                )
            except Exception as err:
                _LOGGER.error("Error during configuration: %s", err)
                errors["base"] = "unknown"

        # Show configuration form
        data_schema = vol.Schema({
            vol.Optional(CONF_SAFETY_MIN_TEMP, default=DEFAULT_SAFETY_MIN_TEMP): 
                selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=32, max=80, mode=selector.NumberSelectorMode.BOX
                    )
                ),
            vol.Optional(CONF_SAFETY_MAX_TEMP, default=DEFAULT_SAFETY_MAX_TEMP):
                selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=60, max=100, mode=selector.NumberSelectorMode.BOX
                    )
                ),
            vol.Optional(CONF_HOME_TEMP, default=DEFAULT_HOME_TEMP):
                selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=50, max=85, mode=selector.NumberSelectorMode.BOX
                    )
                ),
            vol.Optional(CONF_AWAY_TEMP, default=DEFAULT_AWAY_TEMP):
                selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=50, max=85, mode=selector.NumberSelectorMode.BOX
                    )
                ),
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
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=32, max=80, mode=selector.NumberSelectorMode.BOX
                )
            ),
            vol.Optional(
                CONF_SAFETY_MAX_TEMP,
                default=self.config_entry.options.get(
                    CONF_SAFETY_MAX_TEMP, DEFAULT_SAFETY_MAX_TEMP
                )
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=60, max=100, mode=selector.NumberSelectorMode.BOX
                )
            ),
        })

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
        )