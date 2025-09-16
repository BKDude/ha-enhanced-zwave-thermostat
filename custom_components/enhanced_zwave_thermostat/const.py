"""Constants for the Enhanced Z-Wave Thermostat integration."""

DOMAIN = "enhanced_zwave_thermostat"
NAME = "Enhanced Z-Wave Thermostat"

# Configuration constants
CONF_THERMOSTATS = "thermostats"
CONF_SELECTED_CLIMATE_ENTITY = "selected_climate_entity"
CONF_SAFETY_MIN_TEMP = "safety_min_temp"
CONF_SAFETY_MAX_TEMP = "safety_max_temp"
CONF_HOME_TEMP = "home_temp"
CONF_AWAY_TEMP = "away_temp"
CONF_SCHEDULE_ENABLED = "schedule_enabled"

# Default values
DEFAULT_SAFETY_MIN_TEMP = 40  # Fahrenheit
DEFAULT_SAFETY_MAX_TEMP = 90  # Fahrenheit
DEFAULT_HOME_TEMP = 72
DEFAULT_AWAY_TEMP = 65

# Services
SERVICE_SET_SCHEDULE = "set_schedule"
SERVICE_SET_HOME_AWAY = "set_home_away"
SERVICE_OVERRIDE_SAFETY = "override_safety"
SERVICE_DEBUG_INFO = "debug_info"
SERVICE_GET_SCHEDULES = "get_schedules"
SERVICE_UPDATE_SCHEDULE = "update_schedule"
SERVICE_DELETE_SCHEDULE = "delete_schedule"
SERVICE_TOGGLE_SCHEDULE = "toggle_schedule"
SERVICE_SET_HOLD = "set_hold"
SERVICE_CLEAR_HOLD = "clear_hold"

# Events
EVENT_SCHEDULE_UPDATED = f"{DOMAIN}_schedule_updated"
EVENT_NEXT_SETPOINT = f"{DOMAIN}_next_setpoint"
EVENT_HOLD_CHANGED = f"{DOMAIN}_hold_changed"

# Attributes
ATTR_SCHEDULE = "schedule"
ATTR_HOME_AWAY_MODE = "home_away_mode"
ATTR_SAFETY_OVERRIDE = "safety_override"
ATTR_ZONE_ID = "zone_id"
ATTR_ENHANCED_SCHEDULES = "enhanced_schedules"
ATTR_NEXT_SETPOINT_TIME = "enhanced_next_setpoint_time"
ATTR_NEXT_SETPOINT_TEMP = "enhanced_next_setpoint_temp"
ATTR_SCHEDULES_COUNT = "enhanced_schedules_count"
ATTR_HOLD_MODE = "enhanced_hold_mode"
ATTR_HOLD_UNTIL = "enhanced_hold_until"
ATTR_HOLD_TEMPERATURE = "enhanced_hold_temperature"