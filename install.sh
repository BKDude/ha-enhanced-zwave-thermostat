#!/bin/bash
# Enhanced Z-Wave Thermostat Installer for Home Assistant
# Automatically installs the integration and Lovelace card

set -e

echo "🏠 Enhanced Z-Wave Thermostat Installer"
echo "===================================================="

# Function to find Home Assistant config directory
find_ha_config() {
    local possible_paths=(
        "$HOME/.homeassistant"
        "/config"
        "$HOME/homeassistant"
        "./config"
    )
    
    for path in "${possible_paths[@]}"; do
        if [[ -d "$path" && -f "$path/configuration.yaml" ]]; then
            echo "$path"
            return 0
        fi
    done
    
    return 1
}

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Find Home Assistant config
if HA_CONFIG=$(find_ha_config); then
    echo "📁 Found Home Assistant config: $HA_CONFIG"
else
    echo "❌ Could not find Home Assistant configuration directory"
    echo "Please ensure Home Assistant is installed and configured"
    exit 1
fi

# Install integration
echo ""
echo "📦 Installing integration..."
mkdir -p "$HA_CONFIG/custom_components"

if [[ -d "$HA_CONFIG/custom_components/enhanced_zwave_thermostat" ]]; then
    echo "⚠️  Integration already exists. Updating..."
    rm -rf "$HA_CONFIG/custom_components/enhanced_zwave_thermostat"
fi

cp -r "$SCRIPT_DIR/custom_components/enhanced_zwave_thermostat" "$HA_CONFIG/custom_components/"
echo "✅ Integration installed successfully"

# Install card
echo ""
echo "🎨 Installing Lovelace card..."
mkdir -p "$HA_CONFIG/www"
cp "$SCRIPT_DIR/www/enhanced-thermostat-card.js" "$HA_CONFIG/www/"
echo "✅ Lovelace card installed successfully"

echo ""
echo "🎉 Installation completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Restart Home Assistant"
echo "2. Go to Settings > Devices & Services"
echo "3. Click 'Add Integration' and search for 'Enhanced Z-Wave Thermostat'"
echo "4. Add the card resource: /local/enhanced-thermostat-card.js (JavaScript Module)"
echo "5. Add the card to your dashboard"