"""Enhanced Z-Wave Thermostat integration for Home Assistant."""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.CLIMATE]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Enhanced Z-Wave Thermostat from a config entry."""
    _LOGGER.info("Setting up Enhanced Z-Wave Thermostat integration")
    
    try:
        # Store configuration data
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.entry_id] = {}
        
        # Copy card file to www directory (non-blocking)
        try:
            await _ensure_card_file_exists(hass)
        except Exception as card_err:
            _LOGGER.warning("Could not setup card file: %s", card_err)
            # Don't fail the whole setup if card copying fails
        
        # Set up services (skip if running in test mode)
        if not getattr(hass, "_test_mode", False):
            try:
                from .services import async_setup_services
                await async_setup_services(hass)
            except Exception as service_err:
                _LOGGER.warning("Could not setup services: %s", service_err)
                # Don't fail the whole setup if services fail
        
        # Forward the setup to the climate platform
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        
        _LOGGER.info("Enhanced Z-Wave Thermostat integration setup completed successfully")
        return True
        
    except Exception as err:
        _LOGGER.error("Error setting up Enhanced Z-Wave Thermostat integration: %s", err, exc_info=True)
        return False


async def _ensure_card_file_exists(hass: HomeAssistant) -> None:
    """Ensure the Lovelace card file exists in the www directory."""
    import os
    import shutil
    from pathlib import Path
    
    try:
        # Get the component directory
        component_dir = Path(__file__).parent
        card_source = component_dir / "www" / "enhanced-thermostat-card.js"
        
        # Get Home Assistant config directory
        config_dir = Path(hass.config.config_dir)
        www_dir = config_dir / "www"
        card_dest = www_dir / "enhanced-thermostat-card.js"
        
        # Create www directory if it doesn't exist
        www_dir.mkdir(exist_ok=True)
        
        # Copy card file if it doesn't exist or if source is newer
        if card_source.exists():
            if not card_dest.exists() or card_source.stat().st_mtime > card_dest.stat().st_mtime:
                shutil.copy2(card_source, card_dest)
                _LOGGER.info("Copied enhanced-thermostat-card.js to www directory")
                
                # Try to register the resource automatically
                await _register_card_resource(hass)
        else:
            _LOGGER.warning("Card source file not found: %s", card_source)
            
    except Exception as e:
        _LOGGER.warning("Could not copy card file: %s", e)


async def _register_card_resource(hass: HomeAssistant) -> None:
    """Attempt to register the card resource automatically."""
    try:
        # Check if the frontend integration is available
        if "frontend" not in hass.config.components:
            _LOGGER.debug("Frontend integration not available, skipping resource registration")
            return
            
        # Create a persistent notification to remind user about manual resource registration
        hass.components.persistent_notification.async_create(
            title="Enhanced Z-Wave Thermostat Setup",
            message=(
                "Enhanced Z-Wave Thermostat installed successfully!\n\n"
                "**Next step**: Add the Lovelace card resource:\n"
                "1. Go to Settings → Dashboards → Resources\n"
                "2. Click '+ Add Resource'\n"
                "3. URL: `/local/enhanced-thermostat-card.js`\n"
                "4. Type: JavaScript Module\n"
                "5. Click 'Create'\n\n"
                "Then you can add the card to your dashboard!"
            ),
            notification_id="enhanced_zwave_thermostat_setup"
        )
        _LOGGER.info("Created setup notification for card resource registration")
        
    except Exception as e:
        _LOGGER.debug("Could not create setup notification: %s", e)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading Enhanced Z-Wave Thermostat integration")
    
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok