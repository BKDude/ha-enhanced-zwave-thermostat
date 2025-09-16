"""Constants for the Enhanced Z-Wave Thermostat integration."""

DOMAIN = "enhanced_zwave_thermostat"
NAME = "Enhanced Z-Wave Thermostat"

# Configuration constants
CONF_THERMOSTATS = "thermostats"
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

# Attributes
ATTR_SCHEDULE = "schedule"
ATTR_HOME_AWAY_MODE = "home_away_mode"
ATTR_SAFETY_OVERRIDE = "safety_override"
ATTR_ZONE_ID = "zone_id"