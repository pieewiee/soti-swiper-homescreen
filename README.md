# SOTI MobiControl Homescreen Template

![Demo](https://raw.githubusercontent.com/pieewiee/soti-swiper-homescreen/refs/heads/main/demo.gif)

A modern, configurable homescreen template for SOTI MobiControl with Swiper.js navigation and comprehensive device information modals.

## Features

- 🎨 **Modern Design**: Clean, professional interface with customizable branding
- 📱 **Responsive Layout**: Optimized for mobile devices with portrait/landscape support
- 🔄 **Swiper Navigation**: Smooth touch-based app navigation with pagination
- ⚙️ **Configurable**: Extensive customization through JSON configuration
- 📊 **Device Information**: Optional device info modal with toggleable fields
- 🌐 **Offline Ready**: Self-contained with embedded dependencies
- 🎯 **SOTI Compatible**: Full support for SOTI MobiControl variables and deployment

## Quick Start

1. **Configure**: Edit `config.json` to customize branding and features
2. **Build**: Run `.\build-offline-template.ps1` to generate the template
3. **Deploy**: Upload the generated HTML file to SOTI MobiControl

## Configuration

### Basic Template Settings

```json
{
  "template": {
    "title": "Your Company - Mobile Control",
    "headerText": "Your Company Name",
    "footerText": "Device ID: XXXX",
    "footerBadge": "Your Profile"
  }
}
```

### Branding Customization

```json
{
  "branding": {
    "colors": {
      "primary": "#08312A",
      "secondary": "#00E47C", 
      "neutral": "#E5E3DE",
      "surface": "#ffffff"
    },
    "logoUrl": "https://your-domain.com/logo.png",
    "logoFallback": "YC"
  }
}
```

### App Grid Configuration

```json
{
  "apps": {
    "gridColumns": {
      "mobile": 3,
      "tablet": 3
    },
    "gridRows": {
      "mobile": 3,
      "tablet": 3
    }
  }
}
```

## Device Information Modal

The template includes a configurable device information modal that displays SOTI device variables.

### Enabling/Disabling the Modal

```json
{
  "deviceInfo": {
    "enabled": true,
    "title": "Device Information"
  }
}
```

### Available Information Categories

- **Hardware**: Device ID, Manufacturer, Model, Platform, Serial Number
- **Network**: MAC Address, IP Address
- **Cellular**: IMEI, IMSI, ICCID, ESN, Phone Number
- **User**: Username, Email, Domain, UPN
- **Storage**: SD Card information

### Category Configuration

```json
{
  "deviceInfo": {
    "categories": {
      "hardware": {
        "enabled": true,
        "title": "Hardware Information",
        "icon": "bi-cpu",
        "fields": {
          "deviceId": {
            "enabled": true,
            "label": "Device ID",
            "variable": "%DeviceID%"
          }
        }
      }
    }
  }
}
```

## Build Process

### Standard Build
```powershell
.\build-offline-template.ps1
```

### Custom Configuration
```powershell
.\build-offline-template.ps1 -ConfigPath "custom-config.json"
```

### Demo Mode
```powershell
.\build-offline-template.ps1 -DemoMode
```

Demo mode populates the template with sample app data for testing and preview purposes.

## Deployment

1. **Generate Template**: Run the PowerShell build script
2. **Upload to SOTI**: Import the generated HTML file into SOTI MobiControl
3. **Configure Apps**: Set up your applications in SOTI to populate the slots
4. **Deploy**: Push the homescreen to your managed devices

## SOTI Integration

The template supports all standard SOTI MobiControl features:

- **App Slots**: 20 configurable application slots (0-19)
- **SOTI Variables**: Full support for device variables like `%DeviceID%`, `%MANUFACTURER%`, etc.
- **Launch URLs**: Compatible with SOTI app launch mechanisms
- **Responsive Design**: Automatic adaptation to device orientation

### SOTI Variables Used

```
<MCLink0> through <MCLink19>    - App launch URLs
<MCDISP0> through <MCDISP19>    - App display names  
<MCExeIcon0> through <MCExeIcon19> - App icons
%DeviceID%, %MANUFACTURER%, %MODEL% - Device information
%ENROLLEDUSER_USERNAME%, %ENROLLEDUSER_EMAIL% - User details
```

## Technical Specifications

- **Framework**: Bootstrap 5.3.2 + Swiper.js 11
- **Compatibility**: Modern mobile browsers, SOTI MobiControl
- **Dependencies**: Self-contained (all dependencies embedded)
- **File Size**: ~800KB (fully offline-ready)
- **Performance**: Optimized for mobile devices

## Color Themes

The template includes several pre-configured color themes:

### Corporate Blue
```json
{
  "primary": "#1E3A8A",
  "secondary": "#3B82F6",
  "success": "#059669",
  "surface": "#F8FAFC"
}
```

### Healthcare
```json
{
  "primary": "#0369A1", 
  "secondary": "#0D9488",
  "success": "#16A34A",
  "surface": "#FEFEFE"
}
```

### Tech Modern
```json
{
  "primary": "#374151",
  "secondary": "#8B5CF6", 
  "success": "#22C55E",
  "surface": "#F1F5F9"
}
```

## Security Features

- **Configurable Information Display**: Show only necessary device details
- **No External Dependencies**: All resources embedded for security
- **Flexible Privacy Controls**: Enable/disable sensitive information categories

## Browser Support

- Chrome/Chromium (recommended)
- Safari (iOS/iPadOS)
- Edge
- Firefox (mobile)

## Files Structure

```
├── config.json                    # Main configuration file
├── soti-final-lockdown-homescreen.html # Source template
├── build-offline-template.ps1     # Build script
├── demo-homescreen.html           # Demo output
└── soti-final-lockdown-homescreen-offline.html # Production output
```

## License

This template is provided as-is for use with SOTI MobiControl deployments. Customize and deploy according to your organization's requirements.

## Support

For customization assistance or deployment questions, refer to the SOTI MobiControl documentation or consult with your mobile device management administrator.
