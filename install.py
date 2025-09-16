#!/usr/bin/env python3
"""
Enhanced Z-Wave Thermostat Installer for Home Assistant
Automatically installs the integration and Lovelace card
"""
import os
import shutil
import sys
from pathlib import Path


def find_ha_config():
    """Find Home Assistant configuration directory."""
    possible_paths = [
        Path.home() / ".homeassistant",
        Path("/config"),  # Home Assistant OS/Docker
        Path.home() / "homeassistant",
        Path.cwd() / "config",
    ]
    
    for path in possible_paths:
        if path.exists() and (path / "configuration.yaml").exists():
            return path
    
    return None


def install_integration(ha_config_path, source_path):
    """Install the custom integration."""
    source_integration = source_path / "custom_components" / "enhanced_zwave_thermostat"
    target_integration = ha_config_path / "custom_components" / "enhanced_zwave_thermostat"
    
    # Create custom_components directory if it doesn't exist
    target_integration.parent.mkdir(exist_ok=True)
    
    # Copy integration files
    if target_integration.exists():
        print("⚠️  Integration already exists. Updating...")
        shutil.rmtree(target_integration)
    
    shutil.copytree(source_integration, target_integration)
    print("✅ Integration installed successfully")


def install_card(ha_config_path, source_path):
    """Install the Lovelace card."""
    source_card = source_path / "www" / "enhanced-thermostat-card.js"
    target_www = ha_config_path / "www"
    target_card = target_www / "enhanced-thermostat-card.js"
    
    # Create www directory if it doesn't exist
    target_www.mkdir(exist_ok=True)
    
    # Copy card file
    shutil.copy2(source_card, target_card)
    print("✅ Lovelace card installed successfully")


def main():
    """Main installation process."""
    print("🏠 Enhanced Z-Wave Thermostat Installer")
    print("=" * 50)
    
    # Get current script directory
    source_path = Path(__file__).parent.absolute()
    
    # Find Home Assistant config directory
    ha_config_path = find_ha_config()
    
    if not ha_config_path:
        print("❌ Could not find Home Assistant configuration directory")
        print("Please ensure Home Assistant is installed and configured")
        sys.exit(1)
    
    print(f"📁 Found Home Assistant config: {ha_config_path}")
    
    try:
        # Install integration
        print("\n📦 Installing integration...")
        install_integration(ha_config_path, source_path)
        
        # Install card
        print("\n🎨 Installing Lovelace card...")
        install_card(ha_config_path, source_path)
        
        print("\n🎉 Installation completed successfully!")
        print("\n📋 Next steps:")
        print("1. Restart Home Assistant")
        print("2. Go to Settings > Devices & Services")
        print("3. Click 'Add Integration' and search for 'Enhanced Z-Wave Thermostat'")
        print("4. Add the card resource: /local/enhanced-thermostat-card.js (JavaScript Module)")
        print("5. Add the card to your dashboard")
        
    except Exception as e:
        print(f"❌ Installation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()