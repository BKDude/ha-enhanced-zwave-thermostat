"""Config flow for Enhanced Z-Wave Thermostat integration."""
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import entity_registry as er
from homeassistant.const import Platform

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

    def __init__(self):
        """Initialize the config flow."""
        self._selected_entity = None

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step - device selection."""
        errors = {}
        
        if user_input is not None:
            try:
                # Store selected entity and move to configuration step
                self._selected_entity = user_input[CONF_SELECTED_CLIMATE_ENTITY]
                return await self.async_step_configure()
            except Exception as err:
                _LOGGER.error("Error during device selection: %s", err, exc_info=True)
                errors["base"] = "cannot_connect"

        # Get available climate entities
        climate_entities = await self._get_climate_entities()
        
        if not climate_entities:
            return self.async_abort(reason="no_climate_entities")

        # Show device selection form
        data_schema = vol.Schema({
            vol.Required(CONF_SELECTED_CLIMATE_ENTITY): vol.In(climate_entities),
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_configure(self, user_input=None) -> FlowResult:
        """Handle the configuration step."""
        errors = {}
        
        if user_input is not None:
            try:
                # Validate temperature ranges
                min_temp = user_input.get(CONF_SAFETY_MIN_TEMP, DEFAULT_SAFETY_MIN_TEMP)
                max_temp = user_input.get(CONF_SAFETY_MAX_TEMP, DEFAULT_SAFETY_MAX_TEMP)
                
                if min_temp >= max_temp:
                    errors["base"] = "invalid_temp_range"
                else:
                    # Check if this climate entity is already configured
                    existing_entries = self._async_current_entries()
                    for entry in existing_entries:
                        if entry.data.get(CONF_SELECTED_CLIMATE_ENTITY) == self._selected_entity:
                            return self.async_abort(reason="already_configured")
                    
                    # Combine entity selection with configuration
                    final_data = {
                        CONF_SELECTED_CLIMATE_ENTITY: self._selected_entity,
                        **user_input
                    }
                    
                    return self.async_create_entry(
                        title=f"Enhanced Z-Wave Thermostat ({self._selected_entity})",
                        data=final_data
                    )
            except Exception as err:
                _LOGGER.error("Error during configuration: %s", err, exc_info=True)
                errors["base"] = "cannot_connect"

        # Get the friendly name of the selected entity
        entity_registry = er.async_get(self.hass)
        entity_entry = entity_registry.async_get(self._selected_entity)
        friendly_name = entity_entry.name or self._selected_entity if entity_entry else self._selected_entity

        # Show configuration form
        data_schema = vol.Schema({
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
            step_id="configure",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={"entity_name": friendly_name}
        )

    async def _get_climate_entities(self) -> dict:
        """Get available climate entities."""
        climate_entities = {}
        
        # Get entity registry
        entity_registry = er.async_get(self.hass)
        
        # Find all climate entities
        for entity_entry in entity_registry.entities.values():
            if entity_entry.platform == Platform.CLIMATE.value:
                # Get the state to check if entity is available
                state = self.hass.states.get(entity_entry.entity_id)
                if state and state.state not in ["unavailable", "unknown"]:
                    # Use friendly name if available, otherwise entity_id
                    friendly_name = entity_entry.name or state.attributes.get("friendly_name") or entity_entry.entity_id
                    climate_entities[entity_entry.entity_id] = f"{friendly_name} ({entity_entry.entity_id})"
        
        # Also check for climate entities that might not be in the registry
        for entity_id, state in self.hass.states.async_all().items():
            if (entity_id.startswith("climate.") and 
                entity_id not in climate_entities and 
                state.state not in ["unavailable", "unknown"]):
                friendly_name = state.attributes.get("friendly_name") or entity_id
                climate_entities[entity_id] = f"{friendly_name} ({entity_id})"
        
        return climate_entities

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