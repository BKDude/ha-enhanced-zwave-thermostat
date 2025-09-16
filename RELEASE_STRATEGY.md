# Release Strategy for Enhanced Z-Wave Thermostat

## GitHub Repository Setup

1. **Create Repository**
   - Repository name: `enhanced-zwave-thermostat-complete`
   - Make it public
   - Initialize with README.md (use the existing one)

2. **Update URLs in Manifest**
   - Replace `YOUR_USERNAME` in `manifest.json` with your GitHub username
   - Replace `YOUR_USERNAME` in `@YOUR_USERNAME` codeowners with your GitHub username

## Release Process

### Version 1.0.0 (Initial Release)

1. **Upload to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial release v1.0.0 - Enhanced Z-Wave Thermostat"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/enhanced-zwave-thermostat-complete.git
   git push -u origin main
   ```

2. **Create Release**
   - Go to GitHub > Releases > Create a new release
   - Tag: `v1.0.0`
   - Title: `Enhanced Z-Wave Thermostat v1.0.0`
   - Description:
     ```markdown
     # Enhanced Z-Wave Thermostat v1.0.0
     
     🏠 Complete package with integration and Lovelace card!
     
     ## Features
     - ✅ Automatic Z-Wave thermostat discovery
     - ✅ Safety temperature limits
     - ✅ Home/Away presets
     - ✅ Complete scheduling system
     - ✅ Modern Lovelace card with integrated scheduling
     
     ## Installation via HACS
     1. Add this repository as a custom repository in HACS
     2. Install "Enhanced Z-Wave Thermostat (Complete)"
     3. Restart Home Assistant
     4. Add integration via Settings > Integrations
     
     ## Manual Installation
     Run the installer script:
     - **Python**: `python install.py`
     - **Linux/macOS**: `./install.sh`
     
     ## Requirements
     - Home Assistant 2024.3.0+
     - Z-Wave JS integration
     - Z-Wave thermostat devices
     ```

3. **Attach Release Assets** (Optional)
   - Create a zip file of the entire project
   - Attach it to the release

### Future Releases

- Use semantic versioning (1.0.1, 1.1.0, 2.0.0)
- Update version in `manifest.json`
- Create release notes describing changes
- Tag releases appropriately

## HACS Installation Methods

### Method 1: Official HACS Store (Future)
- Submit to HACS for inclusion in the default store
- Requires meeting HACS quality standards
- Takes time for approval

### Method 2: Custom Repository (Immediate)
Users can add your repository manually:
1. HACS > Integrations > ⋮ > Custom repositories
2. Repository: `https://github.com/YOUR_USERNAME/enhanced-zwave-thermostat-complete`
3. Category: Integration
4. Add and install

## Files Required for HACS

✅ All required files are present:
- `hacs.json` (root level)
- `manifest.json` (in integration folder)
- `README.md` (documentation)
- Integration code in `custom_components/`
- Lovelace card in `www/`

## Quality Checklist

Before releasing:
- [ ] Update GitHub URLs in manifest.json
- [ ] Test installation on clean Home Assistant instance
- [ ] Verify HACS installation works
- [ ] Check all documentation links
- [ ] Ensure version numbers are consistent
- [ ] Test with actual Z-Wave thermostats

## Post-Release

1. **Test HACS Installation**
   - Add as custom repository
   - Install and verify functionality
   - Document any issues

2. **Update Documentation**
   - Add screenshots to README
   - Create wiki pages if needed
   - Update troubleshooting section

3. **Monitor Issues**
   - Respond to GitHub issues
   - Update based on user feedback
   - Plan future releases