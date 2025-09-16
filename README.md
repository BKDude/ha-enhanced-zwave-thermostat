# Enhanced Z-Wave Thermostat

An advanced Home Assistant integration that provides enhanced control and monitoring for Z-Wave thermostats with features like automatic scheduling, intelligent temperature management, and a beautiful Lovelace card interface.

## Features

- **Enhanced Climate Control**: Advanced temperature management with schedule-based automation
- **Smart Scheduling**: Automatic temperature adjustments based on time of day
- **Z-Wave Integration**: Seamless integration with existing Z-Wave thermostats
- **Beautiful UI**: Custom Lovelace card with intuitive controls
- **HACS Support**: Easy installation and updates through HACS

## Installation

### HACS Installation (Recommended)

1. **Install via HACS**:
   - Open HACS in Home Assistant
   - Go to "Integrations"
   - Click the 3-dot menu → "Custom repositories"
   - Add repository: `https://github.com/BKDude/ha-enhanced-zwave-thermostat`
   - Category: "Integration"
   - Click "Add"
   - Find "Enhanced Z-Wave Thermostat" and click "Download"

2. **Restart Home Assistant**

3. **Add the Integration**:
   - Go to Settings → Devices & Services → Integrations
   - Click "Add Integration"
   - Search for "Enhanced Z-Wave Thermostat"
   - Follow the setup wizard

4. **Set up the Lovelace Card**:
   - After installation, you'll see a notification with instructions
   - Go to Settings → Dashboards → Resources
   - Click "+ Add Resource"
   - URL: `/local/enhanced-thermostat-card.js`
   - Resource type: JavaScript Module
   - Click "Create"

5. **Add Card to Dashboard**:
   - Go to your dashboard
   - Click "Edit Dashboard"
   - Click "+ Add Card"
   - Find "Enhanced Thermostat Card"
   - Configure with your thermostat entity

### Manual Installation

If you prefer not to use HACS:

1. **Download the Files**:
   ```bash
   cd /config/custom_components
   git clone https://github.com/BKDude/ha-enhanced-zwave-thermostat.git enhanced_zwave_thermostat
   ```

2. **Copy the Card File**:
   ```bash
   cp enhanced_zwave_thermostat/www/enhanced-thermostat-card.js /config/www/
   ```

3. **Restart Home Assistant**

4. **Follow steps 3-5 from HACS installation above**

## Configuration

### Basic Configuration

The integration will automatically discover Z-Wave thermostats on your network. You can configure additional settings through the integration's options:

- **Schedule Management**: Set up automatic temperature schedules
- **Temperature Ranges**: Configure min/max temperature limits
- **Update Intervals**: Adjust how often the thermostat state is refreshed

### Lovelace Card Configuration

Add this to your dashboard configuration:

```yaml
type: custom:enhanced-thermostat-card
entity: climate.your_thermostat_name
show_schedule: true
show_humidity: true
temperature_unit: "°F"  # or "°C"
```

#### Card Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `entity` | string | **Required** | Your thermostat entity ID |
| `show_schedule` | boolean | `true` | Show schedule controls |
| `show_humidity` | boolean | `true` | Show humidity information |
| `temperature_unit` | string | `"°F"` | Temperature unit display |
| `theme` | string | `"default"` | Card theme |

## Advanced Features

### Automatic Scheduling

Set up intelligent temperature schedules:

```yaml
# In your automations.yaml or through the UI
- alias: "Morning Warmup"
  trigger:
    - platform: time
      at: "06:00:00"
  action:
    - service: enhanced_zwave_thermostat.set_schedule
      target:
        entity_id: climate.living_room_thermostat
      data:
        temperature: 72
        hold_until: "08:00:00"
```

### Service Calls

The integration provides several custom services:

#### `enhanced_zwave_thermostat.set_schedule`
Set a temporary schedule override.

#### `enhanced_zwave_thermostat.clear_schedule`
Clear all schedule overrides.

#### `enhanced_zwave_thermostat.force_update`
Force an immediate state refresh.

## Troubleshooting

### Card Not Loading
If you see "Custom element doesn't exist: enhanced-thermostat-card":

1. Check that the resource is properly registered:
   - Settings → Dashboards → Resources
   - Verify `/local/enhanced-thermostat-card.js` is listed

2. Clear your browser cache:
   - Press Ctrl+F5 (or Cmd+Shift+R on Mac)
   - Or disable cache in browser dev tools

3. Check browser console for errors:
   - Press F12 → Console tab
   - Look for JavaScript errors

### Integration Not Found
1. Verify the files are in the correct location:
   ```
   /config/custom_components/enhanced_zwave_thermostat/
   ```

2. Check Home Assistant logs:
   - Settings → System → Logs
   - Look for "enhanced_zwave_thermostat" entries

3. Restart Home Assistant completely

### Z-Wave Thermostat Not Detected
1. Ensure your Z-Wave integration is working
2. Check that your thermostat appears in Z-Wave JS UI
3. Verify the device is properly included in your Z-Wave network

## Development

### Local Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/BKDude/ha-enhanced-zwave-thermostat.git
   cd ha-enhanced-zwave-thermostat
   ```

2. **Install development dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run tests**:
   ```bash
   python -m pytest tests/
   ```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## Support

- **Issues**: [GitHub Issues](https://github.com/BKDude/ha-enhanced-zwave-thermostat/issues)
- **Discussions**: [GitHub Discussions](https://github.com/BKDude/ha-enhanced-zwave-thermostat/discussions)
- **Home Assistant Community**: [Forum Thread](https://community.home-assistant.io/)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

### v1.0.0
- Initial release
- Basic thermostat control
- Custom Lovelace card
- Schedule management
- HACS support