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

## Known Limitations

- **Select/preset state values are not translated.** Config flow field labels are translated (en/fr/nb), but the state values themselves (e.g. `Ready`, `Rest`, `Ready in Rest`, `Low`, `High`, `30 min`) are always shown in English, since they are used directly as internal values rather than translation keys. Fixing this for real would mean switching every select/preset to stable snake_case keys (`ready`, `rest`, ...) plus a `state_attributes` translation block per entity, across all select entities consistently - a dedicated iteration on its own.

## Version History

### v0.3.1 (In Development)
- **Objective:** Align the heat mode / HVAC mode mapping with the official Home Assistant Core Balboa integration
- `Rest` now maps to `HVACMode.OFF` instead of `COOL` (a spa never actively cools, so `COOL` was misleading; `OFF` matches `pybalboa`/HA Core's own mapping)
- `Ready in Rest` now maps to `HVACMode.AUTO`. Unlike the official HA Core integration, `AUTO` is kept in `hvac_modes` (not removed) so the thermostat card correctly reflects the state when the spa enters "Ready in Rest" on its own — but it still can't be selected directly (doing so is a no-op, since there's no command to force that state)
- The "Heat Mode" select entity no longer offers "Ready in Rest" as a settable option (it can still be *displayed* when active), fixing a bug where selecting it only sent a blind Ready/Rest toggle instead of actually reaching that state
- `set_heat_mode()` now sends the toggle command twice when transitioning from "Ready in Rest" to "Ready", to reliably land on the requested state (mirrors `pybalboa`'s `HeatModeSpaControl.set_state` logic)
- The thermostat entity now also exposes a **preset** (`ClimateEntityFeature.PRESET_MODE`) showing the spa's own heat mode names directly on the card ("Ready" / "Rest" / "Ready in Rest"), alongside the HVAC mode. The standalone "Heat Mode" select entity has been removed, as it's now redundant with this preset
- The "Temperature Range" switch has been converted to a select entity with two options (`Low` / `High`), for consistency with the other select-based settings

### v0.3.0 (In Development)
- **Objective:** Rework entities (heat modes, temperature range, LEDs) and adapt the config flow to all current options
- **LED color control**: new `light_mode` option lets you choose between:
  - `switch` (default): simple on/off lights, unchanged from before
  - `color`: each light becomes a select entity offering a configurable color palette. Colors are selected by rapidly toggling the light a fixed number of times (reverse-engineered LED cycling behavior, not documented in the protocol)
- New options flow steps to manage the LED palette: add/edit/delete colors (name, cycle count, RGB for display), reset to default palette, and configure the on/off pulse delays plus the cycle-reset delay (in seconds, default 3s)

### v0.2.3 (In Development)
- **Objective:** Improve logging to support finer diagnosis of recurring disconnections
- Clear separation between **normal logs (INFO)** — connection established, options changed — and **debug logs**
- **Outbound commands (TX)**: every command sent is now logged natively (name + decoded arguments, e.g. `Toggle Item Command (Pump 2)`), replacing the previous fragile monkey-patch
- **Inbound frames (RX)**: consecutive identical frames are collapsed — the first occurrence is logged immediately, repeats are counted silently, and the count is logged as soon as a different frame arrives
- **Known frames are fully decoded field-by-field** (Status Update, Configuration Response, Information Response, Fault Log Response, etc.); unknown frames are logged as raw hex
- Fault Log Response debug logs now include the decoded human-readable fault message (reusing the existing `FAULT_MSG` table), not just the raw code
- The two undocumented "?Error?" frame types from the balboa_worldwide_app wiki (0xE1, 0xF0) are now flagged distinctly as `Possible Error Frame (undocumented)` in debug logs, instead of blending into generic unknown frames — useful to spot potential disconnection-related signals

### v0.2.2 (In Development)
- **Objective:** Make the integration as passive as possible on the connection to improve stability
- Keep-alive is now **disabled by default** (the spa already pushes status updates on its own; keep-alive is opt-in via integration options)
- Added a configurable **keep-alive frame type** option:
  - `existing_client_request` (default): sends the Existing Client Request frame (`0a bf 04`), which gets a real reply from the WiFi module (Configuration Response) — genuine proof of connection life
  - `minimal`: sends the previous bare frame (`0a bf 00 00 01`), which the module accepts silently without any reply
- Added missing translations for `keepalive_enabled`, `keepalive_interval`, and `socket_timeout` options (en/fr/nb)

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
