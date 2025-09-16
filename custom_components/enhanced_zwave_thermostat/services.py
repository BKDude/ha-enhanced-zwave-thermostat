"""Services for Enhanced Z-Wave Thermostat."""
import logging
from datetime import datetime, time
from typing import Any, Dict, List
import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv, entity_registry as er
from homeassistant.helpers.service import async_register_admin_service
from homeassistant.helpers.storage import Store

from .const import (
    DOMAIN,
    SERVICE_SET_SCHEDULE,
    SERVICE_SET_HOME_AWAY,
    SERVICE_OVERRIDE_SAFETY,
    ATTR_SCHEDULE,
    ATTR_HOME_AWAY_MODE,
    ATTR_ZONE_ID,
)

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}_schedules"

# Service schemas
SET_SCHEDULE_SCHEMA = vol.Schema({
    vol.Required("entity_id"): cv.entity_id,
    vol.Required(ATTR_SCHEDULE): vol.Schema({
        vol.Required("weekdays"): vol.All(cv.ensure_list, [cv.string]),
        vol.Required("time"): cv.string,  # Accept time as string format like "07:00"
        vol.Required("temperature"): vol.Coerce(float),
        vol.Optional("name"): cv.string,
    }),
})

SET_HOME_AWAY_SCHEMA = vol.Schema({
    vol.Required("entity_id"): cv.entity_id,
    vol.Required(ATTR_HOME_AWAY_MODE): vol.In(["home", "away"]),
})

OVERRIDE_SAFETY_SCHEMA = vol.Schema({
    vol.Required("entity_id"): cv.entity_id,
    vol.Required("temperature"): vol.Coerce(float),
    vol.Optional("duration"): vol.Coerce(int),  # Minutes
})


class ScheduleManager:
    """Manage thermostat schedules."""
    
    def __init__(self, hass: HomeAssistant):
        """Initialize the schedule manager."""
        self.hass = hass
        self._store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self._schedules: Dict[str, List[Dict[str, Any]]] = {}
        
    async def async_load(self) -> None:
        """Load schedules from storage."""
        data = await self._store.async_load()
        if data:
            self._schedules = data.get("schedules", {})
        _LOGGER.info("Loaded %d thermostat schedules", len(self._schedules))
        
    async def async_save(self) -> None:
        """Save schedules to storage."""
        await self._store.async_save({"schedules": self._schedules})
        _LOGGER.debug("Saved thermostat schedules")
        
    async def async_set_schedule(self, entity_id: str, schedule: Dict[str, Any]) -> None:
        """Set a schedule for an entity."""
        if entity_id not in self._schedules:
            self._schedules[entity_id] = []
            
        # Add schedule entry
        schedule_entry = {
            "weekdays": schedule["weekdays"],
            "time": schedule["time"].strftime("%H:%M"),
            "temperature": schedule["temperature"],
            "name": schedule.get("name", f"Schedule {len(self._schedules[entity_id]) + 1}"),
            "enabled": True,
            "created": datetime.now().isoformat(),
        }
        
        self._schedules[entity_id].append(schedule_entry)
        await self.async_save()
        
        _LOGGER.info("Added schedule for %s: %s", entity_id, schedule_entry)
        
    def get_schedules(self, entity_id: str) -> List[Dict[str, Any]]:
        """Get schedules for an entity."""
        return self._schedules.get(entity_id, [])
        
    def get_current_scheduled_temperature(self, entity_id: str) -> float | None:
        """Get the current scheduled temperature for an entity."""
        schedules = self.get_schedules(entity_id)
        current_time = datetime.now().time()
        current_weekday = datetime.now().strftime("%A").lower()
        
        # Find matching schedule for current time and day
        for schedule in schedules:
            if not schedule.get("enabled", True):
                continue
                
            schedule_time = datetime.strptime(schedule["time"], "%H:%M").time()
            weekdays = [day.lower() for day in schedule["weekdays"]]
            
            if current_weekday in weekdays and current_time >= schedule_time:
                return schedule["temperature"]
                
        return None


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for Enhanced Z-Wave Thermostat."""
    schedule_manager = ScheduleManager(hass)
    await schedule_manager.async_load()
    
    # Store schedule manager in hass data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["schedule_manager"] = schedule_manager
    
    async def async_set_schedule(call: ServiceCall) -> None:
        """Handle set_schedule service call."""
        try:
            entity_id = call.data["entity_id"]
            schedule = call.data[ATTR_SCHEDULE]
            
            _LOGGER.info("Creating schedule for %s: %s", entity_id, schedule)
            
            # Validate time format
            time_str = schedule["time"]
            try:
                # Parse time to validate format
                time_parts = time_str.split(":")
                if len(time_parts) != 2:
                    raise ValueError("Invalid time format")
                hours, minutes = int(time_parts[0]), int(time_parts[1])
                if not (0 <= hours <= 23 and 0 <= minutes <= 59):
                    raise ValueError("Invalid time values")
            except (ValueError, IndexError) as e:
                _LOGGER.error("Invalid time format '%s': %s", time_str, e)
                raise ValueError(f"Invalid time format '{time_str}'. Use HH:MM format.")
            
            await schedule_manager.async_set_schedule(entity_id, schedule)
            
            # Notify the entity about the new schedule
            entity_registry = er.async_get(hass)
            entity_entry = entity_registry.async_get(entity_id)
            
            if entity_entry and entity_entry.platform == DOMAIN:
                # Trigger an update on the entity
                state = hass.states.get(entity_id)
                if state:
                    hass.bus.async_fire(
                        f"{DOMAIN}_schedule_updated",
                        {"entity_id": entity_id, "schedule": schedule}
                    )
                    _LOGGER.info("Schedule created successfully for %s", entity_id)
            else:
                _LOGGER.warning("Entity %s not found or not from this integration", entity_id)
                
        except Exception as e:
            _LOGGER.error("Failed to create schedule: %s", e)
            raise
    
    async def async_set_home_away(call: ServiceCall) -> None:
        """Handle set_home_away service call."""
        entity_id = call.data["entity_id"]
        mode = call.data[ATTR_HOME_AWAY_MODE]
        
        # Get the entity and set its preset mode
        entity_registry = er.async_get(hass)
        entity_entry = entity_registry.async_get(entity_id)
        
        if entity_entry and entity_entry.platform == DOMAIN:
            await hass.services.async_call(
                "climate",
                "set_preset_mode",
                {"entity_id": entity_id, "preset_mode": mode}
            )
    
    async def async_override_safety(call: ServiceCall) -> None:
        """Handle override_safety service call."""
        entity_id = call.data["entity_id"]
        temperature = call.data["temperature"]
        duration = call.data.get("duration", 60)  # Default 1 hour
        
        _LOGGER.warning(
            "Safety override requested for %s: %s°F for %s minutes",
            entity_id, temperature, duration
        )
        
        # This would implement temporary safety override logic
        # For now, just log the request
        
    # Register services
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_SCHEDULE,
        async_set_schedule,
        schema=SET_SCHEDULE_SCHEMA,
    )
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_HOME_AWAY,
        async_set_home_away,
        schema=SET_HOME_AWAY_SCHEMA,
    )
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_OVERRIDE_SAFETY,
        async_override_safety,
        schema=OVERRIDE_SAFETY_SCHEMA,
    )
    
    _LOGGER.info("Enhanced Z-Wave Thermostat services registered")