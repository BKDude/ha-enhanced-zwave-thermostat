"""Config flow for Enhanced Z-Wave Thermostat integration."""
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)
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
        super().__init__()
        self._climate_entities = []

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step."""
        errors = {}
        
        # Get available climate entities
        await self._get_climate_entities()
        
        _LOGGER.debug("Found %d climate entities: %s", 
                     len(self._climate_entities), 
                     [entity.entity_id for entity in self._climate_entities])
        
        if user_input is not None:
            try:
                # Validate selected entity
                selected_entity = user_input.get(CONF_SELECTED_CLIMATE_ENTITY)
                _LOGGER.info("Config flow received user input: %s", user_input)
                _LOGGER.info("Selected entity: %s", selected_entity)
                
                if not selected_entity:
                    errors["base"] = "no_entity_selected"
                    _LOGGER.warning("No climate entity selected")
                else:
                    # Check if entity exists and is valid
                    entity_registry = er.async_get(self.hass)
                    entity_entry = entity_registry.async_get(selected_entity)
                    
                    _LOGGER.info("Entity registry lookup for %s: %s", selected_entity, entity_entry)
                    
                    if not entity_entry:
                        errors["base"] = "entity_not_found"
                        _LOGGER.error("Selected entity %s not found in registry", selected_entity)
                    elif entity_entry.domain != Platform.CLIMATE.value:
                        errors["base"] = "invalid_entity_type"
                        _LOGGER.error("Selected entity %s is not a climate entity (domain: %s, platform: %s)", 
                                    selected_entity, entity_entry.domain, entity_entry.platform)
                    else:
                        _LOGGER.info("Entity validation passed for %s (domain: %s, platform: %s)", 
                                   selected_entity, entity_entry.domain, entity_entry.platform)
                        # Check if this entity is already configured
                        await self._check_existing_entries(selected_entity, errors)
                        
                        if not errors:
                            # Temperature validation
                            min_temp = user_input.get(CONF_SAFETY_MIN_TEMP, DEFAULT_SAFETY_MIN_TEMP)
                            max_temp = user_input.get(CONF_SAFETY_MAX_TEMP, DEFAULT_SAFETY_MAX_TEMP)
                            
                            if min_temp >= max_temp:
                                errors["base"] = "invalid_temp_range"
                                _LOGGER.error("Invalid temperature range: min=%s, max=%s", min_temp, max_temp)
                            else:
                                # Create unique title based on entity
                                entity_name = entity_entry.name or entity_entry.original_name or selected_entity
                                title = f"Enhanced Z-Wave Thermostat ({entity_name})"
                                
                                _LOGGER.info("Creating config entry for entity %s with title: %s", 
                                           selected_entity, title)
                                
                                return self.async_create_entry(
                                    title=title,
                                    data=user_input
                                )
                                
            except Exception as err:
                _LOGGER.error("Error during configuration: %s", err, exc_info=True)
                errors["base"] = "unknown_error"

        # Check if no climate entities are available
        if not self._climate_entities:
            _LOGGER.warning("No climate entities found in Home Assistant")
            errors["base"] = "no_climate_entities"

        # Create the form schema
        data_schema = self._create_data_schema()

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "entity_count": str(len(self._climate_entities))
            }
        )

    async def _get_climate_entities(self):
        """Get all available climate entities."""
        try:
            entity_registry = er.async_get(self.hass)
            self._climate_entities = [
                entry for entry in entity_registry.entities.values()
                if entry.domain == Platform.CLIMATE.value
                and not entry.disabled_by
                and not entry.hidden_by
            ]
            
            _LOGGER.debug("Registry scan complete. Found entities: %s", 
                         [(e.entity_id, e.name, e.platform) for e in self._climate_entities])
                         
        except Exception as err:
            _LOGGER.error("Error getting climate entities: %s", err, exc_info=True)
            self._climate_entities = []

    async def _check_existing_entries(self, entity_id: str, errors: dict):
        """Check if entity is already configured."""
        for entry in self._async_current_entries():
            if entry.data.get(CONF_SELECTED_CLIMATE_ENTITY) == entity_id:
                errors["base"] = "entity_already_configured"
                _LOGGER.warning("Entity %s is already configured in entry %s", 
                              entity_id, entry.entry_id)
                break

    def _create_data_schema(self):
        """Create the data schema for the form."""
        return vol.Schema({
            vol.Required(CONF_SELECTED_CLIMATE_ENTITY): EntitySelector(
                EntitySelectorConfig(
                    domain=Platform.CLIMATE,
                    multiple=False,
                )
            ),
            vol.Optional(CONF_SAFETY_MIN_TEMP, default=DEFAULT_SAFETY_MIN_TEMP): NumberSelector(
                NumberSelectorConfig(
                    min=32,
                    max=80,
                    step=1,
                    mode=NumberSelectorMode.BOX,
                    unit_of_measurement="°F"
                )
            ),
            vol.Optional(CONF_SAFETY_MAX_TEMP, default=DEFAULT_SAFETY_MAX_TEMP): NumberSelector(
                NumberSelectorConfig(
                    min=60,
                    max=100,
                    step=1,
                    mode=NumberSelectorMode.BOX,
                    unit_of_measurement="°F"
                )
            ),
            vol.Optional(CONF_HOME_TEMP, default=DEFAULT_HOME_TEMP): NumberSelector(
                NumberSelectorConfig(
                    min=50,
                    max=85,
                    step=1,
                    mode=NumberSelectorMode.BOX,
                    unit_of_measurement="°F"
                )
            ),
            vol.Optional(CONF_AWAY_TEMP, default=DEFAULT_AWAY_TEMP): NumberSelector(
                NumberSelectorConfig(
                    min=50,
                    max=85,
                    step=1,
                    mode=NumberSelectorMode.BOX,
                    unit_of_measurement="°F"
                )
            ),
        })

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