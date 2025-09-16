"""Services for Enhanced Z-Wave Thermostat.

Initial simple schedule service expanded with:
 - Unique schedule IDs
 - get_schedules service
 - Next setpoint calculation event
 - Central helpers for other modules (climate entity attributes)
"""
import logging
from datetime import datetime, time, timedelta
from typing import Any, Dict, List, Optional
import uuid
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
    SERVICE_DEBUG_INFO,
    SERVICE_GET_SCHEDULES,
    SERVICE_UPDATE_SCHEDULE,
    SERVICE_DELETE_SCHEDULE,
    SERVICE_TOGGLE_SCHEDULE,
    SERVICE_SET_HOLD,
    SERVICE_CLEAR_HOLD,
    ATTR_SCHEDULE,
    ATTR_HOME_AWAY_MODE,
    ATTR_ZONE_ID,
    EVENT_SCHEDULE_UPDATED,
    EVENT_NEXT_SETPOINT,
    EVENT_HOLD_CHANGED,
)

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 2
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

DEBUG_INFO_SCHEMA = vol.Schema({
    vol.Optional("entity_id"): cv.entity_id,
})


class ScheduleManager:
    """Manage thermostat schedules and holds."""

    def __init__(self, hass: HomeAssistant):
        self.hass = hass
        self._store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self._schedules: Dict[str, List[Dict[str, Any]]] = {}
        self._holds: Dict[str, Dict[str, Any]] = {}

    async def async_load(self) -> None:
        data = await self._store.async_load()
        if data:
            self._schedules = data.get("schedules", {})
            self._holds = data.get("holds", {})
        changed = False
        for eid, items in self._schedules.items():
            for sch in items:
                if "id" not in sch:
                    sch["id"] = uuid.uuid4().hex
                    changed = True
        if changed:
            await self.async_save()
        _LOGGER.info("Loaded schedules for %d entities (%d holds)", len(self._schedules), len(self._holds))

    async def async_save(self) -> None:
        await self._store.async_save({"schedules": self._schedules, "holds": self._holds})

    def list(self, entity_id: str) -> List[Dict[str, Any]]:
        return self._schedules.get(entity_id, [])

    async def async_add(self, entity_id: str, schedule: Dict[str, Any]) -> Dict[str, Any]:
        self._schedules.setdefault(entity_id, [])
        entry = {
            "id": uuid.uuid4().hex,
            "weekdays": schedule["weekdays"],
            # already validated format HH:MM (string), keep as string
            "time": schedule["time"],
            "temperature": schedule["temperature"],
            "name": schedule.get("name") or f"Schedule {len(self._schedules[entity_id]) + 1}",
            "enabled": True,
            "created": datetime.now().isoformat(),
        }
        self._schedules[entity_id].append(entry)
        await self.async_save()
        return entry

    def current_match(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Return latest schedule whose time has passed today for current weekday."""
        items = self.list(entity_id)
        if not items:
            return None
        now = datetime.now()
        weekday = now.strftime("%A").lower()
        current_time = now.time()
        candidates: List[Dict[str, Any]] = []
        for s in items:
            if not s.get("enabled", True):
                continue
            if weekday not in [d.lower() for d in s.get("weekdays", [])]:
                continue
            try:
                schedule_time = datetime.strptime(s["time"], "%H:%M").time()
            except ValueError:
                continue
            if current_time >= schedule_time:
                candidates.append((schedule_time, s))
        if not candidates:
            return None
        # pick latest time
        candidates.sort(key=lambda x: x[0])
        return candidates[-1][1]

    def next_setpoint(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Compute next setpoint later today or tomorrow."""
        items = self.list(entity_id)
        if not items:
            return None
        now = datetime.now()
        weekday_index = now.weekday()  # Monday=0
        # Build sequence of next 2 days to find next future time
        for day_offset in range(0, 2):
            check_date = now + timedelta(days=day_offset)
            wd = check_date.strftime("%A").lower()
            future: List[tuple[datetime, Dict[str, Any]]] = []
            for s in items:
                if not s.get("enabled", True):
                    continue
                if wd not in [d.lower() for d in s.get("weekdays", [])]:
                    continue
                try:
                    schedule_time = datetime.strptime(s["time"], "%H:%M").time()
                except ValueError:
                    continue
                candidate_dt = datetime.combine(check_date.date(), schedule_time)
                if candidate_dt > now:
                    future.append((candidate_dt, s))
            if future:
                future.sort(key=lambda x: x[0])
                dt, sched = future[0]
                return {
                    "time": dt.isoformat(),
                    "temperature": sched["temperature"],
                    "schedule_id": sched["id"],
                    "name": sched.get("name"),
                }
        return None

    def as_dict(self, entity_id: str) -> Dict[str, Any]:
        return {"schedules": self.list(entity_id), "hold": self.active_hold(entity_id)}

    def _find(self, entity_id: str, schedule_id: str) -> Optional[Dict[str, Any]]:
        for s in self.list(entity_id):
            if s.get("id") == schedule_id:
                return s
        return None

    async def async_update(self, entity_id: str, schedule_id: str, **changes) -> Optional[Dict[str, Any]]:
        sched = self._find(entity_id, schedule_id)
        if not sched:
            return None
        for key in ("weekdays", "time", "temperature", "name"):
            if key in changes and changes[key] is not None:
                sched[key] = changes[key]
        sched["updated"] = datetime.now().isoformat()
        await self.async_save()
        return sched

    async def async_delete(self, entity_id: str, schedule_id: str) -> bool:
        items = self.list(entity_id)
        new_items = [s for s in items if s.get("id") != schedule_id]
        if len(new_items) == len(items):
            return False
        self._schedules[entity_id] = new_items
        await self.async_save()
        return True

    async def async_toggle(self, entity_id: str, schedule_id: str, enabled: bool) -> Optional[Dict[str, Any]]:
        sched = self._find(entity_id, schedule_id)
        if not sched:
            return None
        sched["enabled"] = enabled
        sched["updated"] = datetime.now().isoformat()
        await self.async_save()
        return sched

    async def async_set_hold(self, entity_id: str, mode: str, temperature: float, until: Optional[str]) -> Dict[str, Any]:
        hold = {
            "mode": mode,
            "temperature": temperature,
            "until": until,
            "created": datetime.now().isoformat(),
        }
        self._holds[entity_id] = hold
        await self.async_save()
        return hold

    async def async_clear_hold(self, entity_id: str) -> None:
        if entity_id in self._holds:
            self._holds.pop(entity_id)
            await self.async_save()

    def active_hold(self, entity_id: str) -> Optional[Dict[str, Any]]:
        hold = self._holds.get(entity_id)
        if not hold:
            return None
        until = hold.get("until")
        if until:
            try:
                if datetime.fromisoformat(until) < datetime.now():
                    # Expired hold – remove and persist asynchronously
                    self._holds.pop(entity_id, None)
                    # Fire-and-forget save (don't block attribute reads)
                    self.hass.async_create_task(self.async_save())
                    return None
            except ValueError:
                return hold
        return hold

    # Added to satisfy climate entity usage and unify schedule/hold precedence
    def get_current_scheduled_temperature(self, entity_id: str) -> Optional[float]:
        """Return the effective target temperature now (hold overrides schedule).

        Precedence:
        1. Active hold (temporary or permanent)
        2. Latest matching schedule for today whose time has passed
        3. None (no change)
        """
        hold = self.active_hold(entity_id)
        if hold:
            try:
                return float(hold.get("temperature"))
            except (TypeError, ValueError):  # defensive
                pass
        match = self.current_match(entity_id)
        if match:
            try:
                return float(match.get("temperature"))
            except (TypeError, ValueError):
                return None
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
            
            added = await schedule_manager.async_add(entity_id, schedule)

            # Fire update event
            entity_registry = er.async_get(hass)
            entity_entry = entity_registry.async_get(entity_id)
            
            if entity_entry and entity_entry.platform == DOMAIN:
                hass.bus.async_fire(
                    EVENT_SCHEDULE_UPDATED,
                    {"entity_id": entity_id, "change": "added", "schedule": added},
                )
                # Also compute next setpoint
                next_sp = schedule_manager.next_setpoint(entity_id)
                if next_sp:
                    hass.bus.async_fire(
                        EVENT_NEXT_SETPOINT,
                        {"entity_id": entity_id, **next_sp},
                    )
                _LOGGER.info("Schedule created successfully for %s", entity_id)
            else:
                _LOGGER.warning("Entity %s not found or not from this integration", entity_id)
        except Exception as e:
            _LOGGER.error("Failed to create schedule: %s", e)
            raise

    async def async_get_schedules(call: ServiceCall) -> None:
        """Return schedules via an event response (simple pattern)."""
        entity_id = call.data.get("entity_id")
        if not entity_id:
            _LOGGER.error("get_schedules requires entity_id")
            return
        data = schedule_manager.as_dict(entity_id)
        hass.bus.async_fire(
            EVENT_SCHEDULE_UPDATED,
            {"entity_id": entity_id, "change": "queried", **data},
        )

    async def async_update_schedule(call: ServiceCall) -> None:
        entity_id = call.data.get("entity_id")
        schedule_id = call.data.get("schedule_id")
        if not entity_id or not schedule_id:
            _LOGGER.error("update_schedule requires entity_id and schedule_id")
            return
        sched = await schedule_manager.async_update(
            entity_id,
            schedule_id,
            weekdays=call.data.get("weekdays"),
            time=call.data.get("time"),
            temperature=call.data.get("temperature"),
            name=call.data.get("name"),
        )
        if not sched:
            _LOGGER.warning("Schedule %s not found for %s", schedule_id, entity_id)
            return
        hass.bus.async_fire(
            EVENT_SCHEDULE_UPDATED,
            {"entity_id": entity_id, "change": "updated", "schedule": sched},
        )

    async def async_delete_schedule(call: ServiceCall) -> None:
        entity_id = call.data.get("entity_id")
        schedule_id = call.data.get("schedule_id")
        if not entity_id or not schedule_id:
            _LOGGER.error("delete_schedule requires entity_id and schedule_id")
            return
        removed = await schedule_manager.async_delete(entity_id, schedule_id)
        if removed:
            hass.bus.async_fire(
                EVENT_SCHEDULE_UPDATED,
                {"entity_id": entity_id, "change": "deleted", "schedule_id": schedule_id},
            )
        else:
            _LOGGER.warning("Schedule %s not removed (not found) for %s", schedule_id, entity_id)

    async def async_toggle_schedule(call: ServiceCall) -> None:
        entity_id = call.data.get("entity_id")
        schedule_id = call.data.get("schedule_id")
        enabled = call.data.get("enabled")
        if not entity_id or schedule_id is None or enabled is None:
            _LOGGER.error("toggle_schedule requires entity_id, schedule_id, enabled")
            return
        sched = await schedule_manager.async_toggle(entity_id, schedule_id, bool(enabled))
        if sched:
            hass.bus.async_fire(
                EVENT_SCHEDULE_UPDATED,
                {"entity_id": entity_id, "change": "toggled", "schedule": sched},
            )

    async def async_set_hold(call: ServiceCall) -> None:
        entity_id = call.data.get("entity_id")
        mode = call.data.get("mode", "temporary")
        temperature = call.data.get("temperature")
        until = call.data.get("until")
        if temperature is None:
            _LOGGER.error("set_hold requires temperature")
            return
        hold = await schedule_manager.async_set_hold(entity_id, mode, float(temperature), until)
        hass.bus.async_fire(
            EVENT_HOLD_CHANGED,
            {"entity_id": entity_id, "change": "set", "hold": hold},
        )

    async def async_clear_hold(call: ServiceCall) -> None:
        entity_id = call.data.get("entity_id")
        await schedule_manager.async_clear_hold(entity_id)
        hass.bus.async_fire(
            EVENT_HOLD_CHANGED,
            {"entity_id": entity_id, "change": "cleared"},
        )
    
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
        
    async def async_debug_info(call: ServiceCall) -> None:
        """Handle debug_info service call to help troubleshoot issues."""
        entity_registry = er.async_get(hass)
        
        # Get all climate entities
        climate_entities = [
            entry for entry in entity_registry.entities.values()
            if entry.domain == "climate"
            and not entry.disabled_by
            and not entry.hidden_by
        ]
        
        # Get enhanced thermostat entities
        enhanced_entities = [
            entry for entry in entity_registry.entities.values()
            if entry.platform == DOMAIN
        ]
        
        debug_info = {
            "climate_entities_found": len(climate_entities),
            "climate_entities": [
                {
                    "entity_id": e.entity_id,
                    "name": e.name or e.original_name,
                    "platform": e.platform,
                    "device_id": e.device_id,
                    "disabled": bool(e.disabled_by),
                    "hidden": bool(e.hidden_by),
                }
                for e in climate_entities
            ],
            "enhanced_thermostat_entities": len(enhanced_entities),
            "enhanced_entities": [
                {
                    "entity_id": e.entity_id,
                    "name": e.name or e.original_name,
                    "platform": e.platform,
                    "device_id": e.device_id,
                }
                for e in enhanced_entities
            ],
            "integration_entries": len(hass.config_entries.async_entries(DOMAIN)),
            "entries": [
                {
                    "entry_id": entry.entry_id,
                    "title": entry.title,
                    "data": entry.data,
                    "state": entry.state,
                }
                for entry in hass.config_entries.async_entries(DOMAIN)
            ]
        }
        
        _LOGGER.info("Enhanced Z-Wave Thermostat Debug Info: %s", debug_info)
        
        # Also log to a specific debug service call
        _LOGGER.info("=== ENHANCED Z-WAVE THERMOSTAT DEBUG ===")
        _LOGGER.info("Climate entities found: %d", len(climate_entities))
        for entity in climate_entities:
            _LOGGER.info(
                "  - %s (%s) [%s] disabled=%s hidden=%s",
                entity.entity_id,
                entity.name or entity.original_name or "No Name",
                entity.platform,
                bool(entity.disabled_by),
                bool(entity.hidden_by)
            )
        
        _LOGGER.info("Enhanced thermostat entities: %d", len(enhanced_entities))
        for entity in enhanced_entities:
            _LOGGER.info("  - %s (%s)", entity.entity_id, entity.name or entity.original_name)
            
        _LOGGER.info("Config entries: %d", len(hass.config_entries.async_entries(DOMAIN)))
        for entry in hass.config_entries.async_entries(DOMAIN):
            _LOGGER.info("  - %s: %s (state: %s)", entry.entry_id, entry.title, entry.state)
            _LOGGER.info("    Data: %s", entry.data)
        
        _LOGGER.info("=== END DEBUG INFO ===")
        
        return debug_info
        
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
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_SCHEDULES,
        async_get_schedules,
        schema=vol.Schema({vol.Required("entity_id"): cv.entity_id}),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_UPDATE_SCHEDULE,
        async_update_schedule,
        schema=vol.Schema({
            vol.Required("entity_id"): cv.entity_id,
            vol.Required("schedule_id"): cv.string,
            vol.Optional("weekdays"): [cv.string],
            vol.Optional("time"): cv.string,
            vol.Optional("temperature"): vol.Coerce(float),
            vol.Optional("name"): cv.string,
        }),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_DELETE_SCHEDULE,
        async_delete_schedule,
        schema=vol.Schema({
            vol.Required("entity_id"): cv.entity_id,
            vol.Required("schedule_id"): cv.string,
        }),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_TOGGLE_SCHEDULE,
        async_toggle_schedule,
        schema=vol.Schema({
            vol.Required("entity_id"): cv.entity_id,
            vol.Required("schedule_id"): cv.string,
            vol.Required("enabled"): cv.boolean,
        }),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_HOLD,
        async_set_hold,
        schema=vol.Schema({
            vol.Required("entity_id"): cv.entity_id,
            vol.Required("temperature"): vol.Coerce(float),
            vol.Optional("mode", default="temporary"): vol.In(["temporary", "permanent"]),
            vol.Optional("until"): cv.string,
        }),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_CLEAR_HOLD,
        async_clear_hold,
        schema=vol.Schema({vol.Required("entity_id"): cv.entity_id}),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_DEBUG_INFO,
        async_debug_info,
        schema=DEBUG_INFO_SCHEMA,
    )
    
    _LOGGER.info("Enhanced Z-Wave Thermostat services registered")