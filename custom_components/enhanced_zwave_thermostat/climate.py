"""Climate platform for Enhanced Z-Wave Thermostat."""
import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
    HVACAction,
)
from homeassistant.components.zwave_js.const import DOMAIN as ZWAVE_JS_DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_TEMPERATURE,
    PRECISION_WHOLE,
    UnitOfTemperature,
    Platform,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers import entity_registry as er, device_registry as dr

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Enhanced Z-Wave Thermostat climate entities."""
    _LOGGER.info("Setting up Enhanced Z-Wave Thermostat climate platform")
    
    # Get entity and device registries
    entity_registry = er.async_get(hass)
    device_registry = dr.async_get(hass)
    
    # Find existing Z-Wave JS climate entities
    entities = []
    
    # Look for Z-Wave JS climate entities in the entity registry
    for entity_id, entity_entry in entity_registry.entities.items():
        if (entity_entry.platform == ZWAVE_JS_DOMAIN and 
            entity_entry.domain == Platform.CLIMATE):
            
            # Get device info
            device_entry = device_registry.async_get(entity_entry.device_id) if entity_entry.device_id else None
            
            if device_entry:
                _LOGGER.info("Found Z-Wave climate entity: %s (%s)", entity_id, device_entry.name)
                
                # Create enhanced wrapper entity
                enhanced_entity = EnhancedZWaveThermostat(
                    hass=hass,
                    config_entry=config_entry,
                    name=f"Enhanced {device_entry.name or entity_entry.name or 'Thermostat'}",
                    unique_id=f"enhanced_{entity_entry.entity_id}",
                    zwave_entity_id=entity_id,
                    device_entry=device_entry
                )
                entities.append(enhanced_entity)
    
    # Only create demo entity in test mode
    if not entities and getattr(hass, "_test_mode", False):
        _LOGGER.info("No Z-Wave climate entities found. Creating demo entity for testing.")
        entities = [
            EnhancedZWaveThermostat(
                hass=hass,
                config_entry=config_entry,
                name="Enhanced Demo Thermostat",
                unique_id="enhanced_demo_thermostat_1",
                zwave_entity_id=None,
                device_entry=None
            )
        ]
    elif not entities:
        _LOGGER.warning("No Z-Wave climate entities found. Install and configure Z-Wave JS integration with thermostat devices first.")
        return
    
    async_add_entities(entities, True)
    _LOGGER.info("Added %d Enhanced Z-Wave Thermostat entities", len(entities))


class EnhancedZWaveThermostat(ClimateEntity):
    """Enhanced Z-Wave Thermostat entity."""
    
    _attr_should_poll = False  # We'll subscribe to state changes instead

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry, name: str, unique_id: str, zwave_entity_id=None, device_entry=None):
        """Initialize the thermostat."""
        self.hass = hass
        self._config_entry = config_entry
        self._attr_name = name
        # Use stable unique ID based on device entry or fallback
        if device_entry:
            self._attr_unique_id = f"enhanced_{device_entry.id}"
        else:
            self._attr_unique_id = unique_id
        self._zwave_entity_id = zwave_entity_id
        self._device_entry = device_entry
        self._state_listener = None
        
        # Initialize attributes
        self._attr_temperature_unit = UnitOfTemperature.FAHRENHEIT
        self._attr_precision = PRECISION_WHOLE
        self._attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.PRESET_MODE
        )
        self._attr_hvac_modes = [
            HVACMode.OFF,
            HVACMode.HEAT,
            HVACMode.COOL,
            HVACMode.HEAT_COOL,
        ]
        self._attr_preset_modes = ["home", "away", "schedule"]
        
        # State variables
        self._current_temperature = 70.0
        self._target_temperature = 72.0
        self._hvac_mode = HVACMode.HEAT_COOL
        self._hvac_action = HVACAction.IDLE
        self._preset_mode = "home"
        
        # Enhanced features
        self._schedule_enabled = False
        self._safety_min_temp = config_entry.data.get("safety_min_temp", 40)
        self._safety_max_temp = config_entry.data.get("safety_max_temp", 90)
        self._home_temp = config_entry.data.get("home_temp", 72)
        self._away_temp = config_entry.data.get("away_temp", 65)
        
        # Set up schedule evaluation listener
        if not getattr(hass, "_test_mode", False):
            self._setup_schedule_listener()
        
        # Device info for Z-Wave devices
        if self._device_entry:
            # Get the first Z-Wave identifier for via_device
            zwave_identifier = None
            for identifier_domain, identifier_id in self._device_entry.identifiers:
                if identifier_domain == ZWAVE_JS_DOMAIN:
                    zwave_identifier = identifier_id
                    break
            
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, f"enhanced_{self._device_entry.id}")},
                name=f"Enhanced {self._device_entry.name}",
                manufacturer=self._device_entry.manufacturer or "Unknown",
                model=f"Enhanced {self._device_entry.model or 'Z-Wave Thermostat'}",
                sw_version=self._device_entry.sw_version,
                via_device=(ZWAVE_JS_DOMAIN, zwave_identifier) if zwave_identifier else None,
            )
        else:
            # Demo device info
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, "demo_thermostat")},
                name="Enhanced Demo Thermostat",
                manufacturer="Enhanced Z-Wave",
                model="Demo Thermostat",
                sw_version="0.1.0",
            )

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        if self._zwave_entity_id:
            # Get current temperature from underlying Z-Wave entity
            state = self.hass.states.get(self._zwave_entity_id)
            if state and state.attributes.get("current_temperature"):
                return float(state.attributes["current_temperature"])
        return self._current_temperature

    @property
    def target_temperature(self) -> float | None:
        """Return the temperature we try to reach."""
        if self._zwave_entity_id:
            # Get target temperature from underlying Z-Wave entity
            state = self.hass.states.get(self._zwave_entity_id)
            if state and state.attributes.get("temperature"):
                return float(state.attributes["temperature"])
        return self._target_temperature

    @property
    def hvac_mode(self) -> HVACMode | None:
        """Return current operation."""
        if self._zwave_entity_id:
            # Get HVAC mode from underlying Z-Wave entity
            state = self.hass.states.get(self._zwave_entity_id)
            if state:
                return HVACMode(state.state) if state.state in [mode.value for mode in HVACMode] else self._hvac_mode
        return self._hvac_mode

    @property
    def hvac_action(self) -> HVACAction | None:
        """Return the current running hvac operation."""
        if self._zwave_entity_id:
            # Get HVAC action from underlying Z-Wave entity
            state = self.hass.states.get(self._zwave_entity_id)
            if state and state.attributes.get("hvac_action"):
                return HVACAction(state.attributes["hvac_action"])
        return self._hvac_action

    @property
    def preset_mode(self) -> str | None:
        """Return the current preset mode."""
        return self._preset_mode

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        return {
            "safety_min_temp": self._safety_min_temp,
            "safety_max_temp": self._safety_max_temp,
            "home_temp": self._home_temp,
            "away_temp": self._away_temp,
            "schedule_enabled": self._schedule_enabled,
        }

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        # Apply safety limits
        if temperature < self._safety_min_temp:
            _LOGGER.warning(
                "Temperature %s below safety minimum %s, setting to minimum",
                temperature, self._safety_min_temp
            )
            temperature = self._safety_min_temp
        elif temperature > self._safety_max_temp:
            _LOGGER.warning(
                "Temperature %s above safety maximum %s, setting to maximum",
                temperature, self._safety_max_temp
            )
            temperature = self._safety_max_temp

        # Delegate to underlying Z-Wave entity if available
        if self._zwave_entity_id:
            await self.hass.services.async_call(
                "climate",
                "set_temperature",
                {
                    "entity_id": self._zwave_entity_id,
                    "temperature": temperature
                }
            )
        else:
            # Demo mode - just update local state
            self._target_temperature = temperature
            
        _LOGGER.info("Setting target temperature to %s", temperature)
        self.async_write_ha_state()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        # Delegate to underlying Z-Wave entity if available
        if self._zwave_entity_id:
            await self.hass.services.async_call(
                "climate",
                "set_hvac_mode",
                {
                    "entity_id": self._zwave_entity_id,
                    "hvac_mode": hvac_mode.value
                }
            )
        else:
            # Demo mode - just update local state
            self._hvac_mode = hvac_mode
            
        _LOGGER.info("Setting HVAC mode to %s", hvac_mode)
        self.async_write_ha_state()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        self._preset_mode = preset_mode
        
        # Apply preset temperatures
        if preset_mode == "home":
            await self.async_set_temperature(temperature=self._home_temp)
        elif preset_mode == "away":
            await self.async_set_temperature(temperature=self._away_temp)
        elif preset_mode == "schedule":
            self._schedule_enabled = True
            
        _LOGGER.info("Setting preset mode to %s", preset_mode)
        self.async_write_ha_state()

    def _setup_schedule_listener(self) -> None:
        """Set up listener for schedule events."""
        from homeassistant.helpers.event import async_track_time_interval
        from datetime import timedelta
        
        # Check schedule every minute
        async def _check_schedule(now):
            """Check if schedule should be applied."""
            if self._schedule_enabled and self._preset_mode == "schedule":
                await self._apply_current_schedule()
        
        # Track time intervals for schedule evaluation
        async_track_time_interval(self.hass, _check_schedule, timedelta(minutes=1))
        
        # Listen for schedule update events
        @callback
        def _schedule_updated_listener(event):
            """Handle schedule update events."""
            if event.data.get("entity_id") == self.entity_id:
                self.hass.async_create_task(self._apply_current_schedule())
        
        self.hass.bus.async_listen(f"{DOMAIN}_schedule_updated", _schedule_updated_listener)

    async def _apply_current_schedule(self) -> None:
        """Apply the current scheduled temperature."""
        if DOMAIN not in self.hass.data or "schedule_manager" not in self.hass.data[DOMAIN]:
            return
            
        schedule_manager = self.hass.data[DOMAIN]["schedule_manager"]
        scheduled_temp = schedule_manager.get_current_scheduled_temperature(self.entity_id)
        
        if scheduled_temp is not None:
            _LOGGER.info("Applying scheduled temperature %s for %s", scheduled_temp, self.entity_id)
            await self.async_set_temperature(temperature=scheduled_temp)

    async def async_added_to_hass(self) -> None:
        """Run when entity is added to hass."""
        await super().async_added_to_hass()
        
        if self._zwave_entity_id:
            # Subscribe to state changes from the underlying Z-Wave entity
            @callback
            def _state_listener(event):
                """Handle state changes from underlying entity."""
                entity_id = event.data.get("entity_id")
                if entity_id == self._zwave_entity_id:
                    # Update our state when the underlying entity changes
                    self.async_write_ha_state()
            
            self._state_listener = self.hass.bus.async_listen(
                "state_changed", _state_listener
            )

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity will be removed from hass."""
        await super().async_will_remove_from_hass()
        
        if self._state_listener:
            self._state_listener()
            self._state_listener = None

    async def async_update(self) -> None:
        """Update the entity."""
        # For demo mode only, simulate some changes
        if not self._zwave_entity_id:
            # Demo mode - simulate temperature fluctuations
            import random
            self._current_temperature += random.uniform(-0.5, 0.5)