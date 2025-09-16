# Enhanced Z-Wave Thermostat (Complete Package)

🏠 **One-Click Installation** - Integration + Lovelace Card in a single package!

This package includes both the Enhanced Z-Wave Thermostat integration and the beautiful Lovelace card for complete thermostat control with scheduling.

## ⚡ Quick Install Options

### Option 1: Automated Script (Recommended)

**Linux/macOS/Docker:**
```bash
# Download and run the installer
./install.sh
```

**Windows/Python:**
```bash
python install.py
```

### Option 2: Manual Installation

1. Copy `custom_components/enhanced_zwave_thermostat/` to your HA `custom_components/` folder
2. Copy `www/enhanced-thermostat-card.js` to your HA `www/` folder
3. Restart Home Assistant
4. Add the integration via Settings > Integrations
5. Add the card resource: `/local/enhanced-thermostat-card.js` (JavaScript Module)

## 🚀 What You Get

### Enhanced Z-Wave Thermostat Integration
- **Automatic Z-Wave Discovery** - Finds your existing thermostats
- **Safety Temperature Limits** - Configurable min/max protection
- **Home/Away Presets** - Energy-saving temperature modes
- **Complete Scheduling System** - Weekly temperature schedules
- **Real-time Synchronization** - Instant updates from Z-Wave devices

### Enhanced Thermostat Card
- **Beautiful Visual Interface** - Modern thermostat design
- **Integrated Scheduling** - Create schedules right in the card
- **One-Touch Controls** - Temperature, mode, and preset buttons
- **Safety Limit Display** - Shows your configured safety ranges
- **Mobile Responsive** - Works perfectly on phones and tablets

## 📋 Setup Instructions

### After Installation:

1. **Restart Home Assistant**

2. **Add the Integration:**
   - Go to Settings > Devices & Services
   - Click "Add Integration"
   - Search for "Enhanced Z-Wave Thermostat"
   - Configure your safety limits and default temperatures

3. **Add the Card Resource:**
   - Go to Settings > Dashboards > Resources
   - Click "Add Resource"
   - URL: `/local/enhanced-thermostat-card.js`
   - Type: JavaScript Module

4. **Add Card to Dashboard:**
   ```yaml
   type: custom:enhanced-thermostat-card
   entity: climate.enhanced_living_room_thermostat
   name: Living Room  # optional
   ```

## 🎯 Card Configuration

### Basic Configuration:
```yaml
type: custom:enhanced-thermostat-card
entity: climate.enhanced_your_thermostat_name
```

### Advanced Configuration:
```yaml
type: custom:enhanced-thermostat-card
entity: climate.enhanced_living_room_thermostat
name: "Living Room Thermostat"
```

## 📱 Using the Scheduling

1. **Click "Add Schedule"** in the card
2. **Fill in the details:**
   - Schedule name (optional)
   - Select days of the week
   - Set time (24-hour format like 07:00)
   - Set target temperature
3. **Click "Save Schedule"**
4. **Schedules apply automatically** when conditions match

## 🔧 Requirements

- Home Assistant 2024.3.0 or newer
- Z-Wave JS integration with thermostat devices
- Modern browser with ES2020 support

## 🆘 Troubleshooting

### Integration Not Found
- Ensure Z-Wave JS integration is installed and working
- Restart Home Assistant after installation
- Check logs in Settings > System > Logs

### Card Not Appearing
- Verify the resource was added correctly
- Hard refresh browser (Ctrl+F5)
- Check browser console for errors

### Schedules Not Working
- Ensure thermostat is in "schedule" preset mode
- Check Home Assistant logs for error messages
- Verify all form fields were filled correctly

## 📄 License

MIT License - Feel free to use, modify, and distribute