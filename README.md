# Balboa Connect - Home Assistant custom component

Balboa Connect for Home Assistant is inspired by several similar projects and the work of many people, including the original SmartSpa Client integration.

If you find this integration useful, you can buy the original author a beer to help keep development going.

[![Buy me a beer](https://img.shields.io/badge/Donate-Buy%20me%20a%20beer-yellow?style=for-the-badge&logo=buy-me-a-coffee)](https://www.buymeacoffee.com/jozefnad)

## What you need

- A Hot Tub Equipped with a Balboa BP System
- SmartSpa Wi-Fi Module, bwa Wi-Fi Module (50350) or custom module with TCP port 4257
- Reference: http://www.balboawatergroup.com/bwa

## Installation

You can install this integration via [HACS](#hacs) or [manually](#manual).

### HACS

Search for the Balboa Connect integration and choose install. Reboot Home Assistant and configure the Balboa Connect integration via the integrations page or press the blue button below.

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=balboa_connect)

### Manual

Copy the `custom_components/balboa_connect` folder to your `custom_components` folder. Reboot Home Assistant and configure the Balboa Connect integration via the integrations page or press the blue button below.

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=balboa_connect)

## Entities

Several elements have already been validated (with my spa), but several remain to be validated with your help. The following tables show what is known to be functional:

### Climate & Temperature Control

Entity | Type | Tested | Description
------ | ---- | ------ | -----------
Spa Thermostat | Climate | ✓ | Full HVAC control with HEAT, COOL, HEAT_COOL modes
Temperature Scale | Select | ✓ | Fahrenheit, Celsius
Clock Mode | Select | ✓ | 12 Hour, 24 Hour
Cleanup Cycle | Select | ✓ | Off, 30-240min intervals
Heat Mode | Select | ✓ | Ready, Rest, Ready in Rest

### Pumps & Jets

Entity | Type | Tested | Description
------ | ---- | ------ | -----------
Pump 1-6 | Switch | ✓ | Off, Low, High
Circulation Pump | Binary Sensor | ✓ | Status
Circulation Pump Status | Switch | ✓ | On/Off

### Heating System

Entity | Type | Tested | Description
------ | ---- | ------ | -----------
Heating State | Sensor | ✓ | Off, Heating, Heat Waiting
Heating | Binary Sensor | ✓ | Active/Inactive
Standby Mode | Switch | ✓ | Enable/Disable heating
Temperature Range | Switch | ✓ | Low, High

### Lights & Features

Entity | Type | Tested | Description
------ | ---- | ------ | -----------
Light 1-2 | Light | ✓ | On/Off, Brightness
Blower | Switch | ✓ | Off, On
Mister | Switch | ? | Off, On
Auxiliary 1-2 | Switch | ? | On/Off

### Filters & Schedules

Entity | Type | Tested | Description
------ | ---- | ------ | -----------
Filter Cycle 1 Status | Binary Sensor | ✓ | Status
Filter Cycle 1 Begins/Run | Time | ✓ | Schedule
Filter Cycle 2 Status | Binary Sensor | ✓ | Status
Filter Cycle 2 | Switch | ✓ | Enable/Disable
Filter Cycle 2 Begins/Run | Time | ✓ | Schedule

### System Status & Sensors

Entity | Type | Tested | Description
------ | ---- | ------ | -----------
Spa State | Sensor | ✓ | Running, Initializing, Hold, Test
WiFi State | Sensor | ✓ | Connection status
Reminder | Sensor | ✓ | Service reminders
Sensor A/B Temperature | Sensor | ✓ | Temperature (°F or °C)
GFCI Test | Sensor | ✓ | Pass/Fail
Model | Sensor | ✓ | Spa model
Software Version | Sensor | ✓ | Version
Heater Power | Sensor | ✓ | Power state

### System Controls & Settings

Entity | Type | Tested | Description
------ | ---- | ------ | -----------
Panel Lock | Switch | ✓ | Lock front panel
Settings Lock | Switch | ✓ | Lock settings menu
Reminders | Switch | ✓ | Enable/disable
M8 AI | Switch | ✓ | AI features
Priming | Binary Sensor | ✓ | Priming status
Notification | Binary Sensor | ✓ | Alarm status

## Heat Mode Mapping

The Spa Thermostat climate entity supports the following HVAC modes, mapped to spa heat modes:

| HVAC Mode | Spa Heat Mode | Description |
|-----------|---------------|-------------|
| HEAT | Ready | Active heating with normal temperature range |
| COOL | Rest | Heating with lower temperature range |
| HEAT_COOL | Ready in Rest | Automatic mode |

Additionally, a dedicated **Heat Mode** select entity allows direct selection between Ready, Rest, and Ready in Rest modes.

## Technical Documentation

### Protocol Overview
- **Communication Protocol:** Binary socket protocol on port 4257
- **Message Checksum:** CRC-8 validation (polynomial 0x07, initial value 0xb5, final XOR 0x02)
- **Status Updates:** 0x13 message type containing 28-32 bytes depending on spa model

### Configuration Flow
1. Connect to spa module on port 4257
2. Receive initial 0x13 status message
3. Parse all state variables and create Home Assistant entities
4. Maintain background read loop for status updates
5. Send keep-alive heartbeat every 30 seconds
6. Process user commands and send appropriate messages with CRC-8 validation

## Entity Statistics

- **Total Sensors:** 14
- **Total Binary Sensors:** 5
- **Total Switches:** 10+
- **Total Select Entities:** 4 (Temperature Scale, Clock Mode, Cleanup Cycle, Heat Mode)
- **Climate Entities:** 1 (Spa Thermostat with HEAT/COOL/HEAT_COOL modes)
- **Light Entities:** 2
- **Time Entities:** 5

## Key Features

### Climate/Thermostat Control
- **Multi-mode HVAC:** HEAT (Ready), COOL (Rest), HEAT_COOL (Ready in Rest)
- **Heating State Monitoring:** Real-time tracking (Off, Heating, Heat Waiting)
- **Temperature Setpoint:** Full control of target water temperature
- **Unit Conversion:** Automatic handling of Fahrenheit/Celsius

### Direct Heat Mode Control
- **Heat Mode Select Entity:** Direct selection between Ready, Rest, Ready in Rest
- **Flexible Control:** Use either Climate entity or Heat Mode select

### Comprehensive Status Monitoring
- **Spa State Sensor:** Running, Initializing, Hold, or Test mode
- **WiFi State Sensor:** Real-time connection status
- **Temperature Sensors:** Separate sensors for Sensor A and B

### Reliability & Protocol Support
- **CRC-8 Validation:** All messages validated with proper checksum
- **Variable Message Lengths:** Support for different spa models
- **Async Socket Communication:** Non-blocking with keep-alive
- **Automatic Reconnection:** Graceful handling of network interruptions

## Version History

### v0.2.1 (In Development)
- Added configurable socket timeout (5-3600s, default: 30s) to handle slow networks
- Improved connection stability with adjustable timeout settings

### v0.2.0
- **Objective:** Stabilize connection handling
- Added configurable keep-alive functionality to prevent module sleep
- Uses recommended frame: `\x0a\xbf\x00\x00\x01`
- Keep-alive can be enabled/disabled via integration options
- Keep-alive interval configurable from 1 to 3600 seconds (1s to 1h)

### v0.1.1
- Added HEAT, COOL, HEAT_COOL mode support to Spa Thermostat climate entity
- Added Heat Mode select entity (Ready, Rest, Ready in Rest)
- Removed Heat Mode switch entity

### v0.1.0
- Renamed integration from SmartSpa Client to Balboa Connect
- Updated all references and documentation
