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
Spa Thermostat | Climate | ✓ | HVAC modes HEAT/OFF (AUTO shown for display only), plus a preset (Ready/Rest/Ready in Rest) showing the spa's own heat mode names directly on the card
Temperature Scale | Select | ✓ | Fahrenheit, Celsius
Clock Mode | Select | ✓ | 12 Hour, 24 Hour
Cleanup Cycle | Select | ✓ | Off, 30-240min intervals

### Pumps & Jets

Entity | Type | Tested | Description
------ | ---- | ------ | -----------
Pump 1-6 | Switch | ✓ | Off, Low, High
Circulation Pump | Binary Sensor | ✓ | Status (only created if detected on your spa)

### Heating System

Entity | Type | Tested | Description
------ | ---- | ------ | -----------
Heating State | Sensor | ✓ | Off, Heating, Heat Waiting
Heating | Binary Sensor | ✓ | Active/Inactive
Standby Mode | Switch | ✓ | Enable/Disable heating
Temperature Range | Select | ✓ | Low, High

### Lights & Features

Entity | Type | Tested | Description
------ | ---- | ------ | -----------
Light 1-2 | Light | ✓ | On/Off only (no brightness/color support) - created when `light_mode` option is `switch` (default)
Light 1-2 Color | Select | ✓ | Color palette, selected by rapidly toggling the light a fixed number of times - created when `light_mode` option is `color` instead of the plain Light entities above
Blower | Switch | ✓ | Off, On
Mister | Switch | ? | Off, On
Auxiliary 1-2 | Switch | ? | On/Off

### Filters & Schedules

Entity | Type | Tested | Description
------ | ---- | ------ | -----------
Filter Cycle 1 Status | Binary Sensor | ✓ | Status
Filter Cycle 1 Begins/Runs | Time | ✓ | Schedule
Filter Cycle 2 Status | Binary Sensor | ✓ | Status
Filter Cycle 2 | Switch | ✓ | Enable/Disable
Filter Cycle 2 Begins/Runs | Time | ✓ | Schedule

### System Status & Sensors

Entity | Type | Tested | Description
------ | ---- | ------ | -----------
Spa State | Sensor | ✓ | Running, Initializing, Hold, Test
Spa Time | Sensor | ✓ | Spa's own clock (hour:minute)
WiFi State | Sensor | ✓ | Connection status
Reminder | Sensor | ✓ | Service reminders
Sensor A/B Temperature | Sensor | ✓ | Temperature (°F or °C)
GFCI Test | Sensor | ✓ | Pass/Fail
Last Known Fault | Sensor | ✓ | Decoded human-readable fault message
Model Name | Sensor | ✓ | Spa model
Software Version | Sensor | ✓ | Version
Heater Voltage | Sensor | ✓ | 240V or Unknown
Heater Type | Sensor | ✓ | Standard or Unknown
Config Signature | Sensor | ✓ | Configuration signature bytes (diagnostic)

### System Controls & Settings

Entity | Type | Tested | Description
------ | ---- | ------ | -----------
Panel Lock | Switch | ✓ | Lock front panel
Settings Lock | Switch | ✓ | Lock settings menu
Reminders | Switch | ✓ | Enable/disable
M8 Artificial Intelligence | Switch | ✓ | AI features
Hold Mode | Switch | ✓ | Pause jets/heater temporarily (e.g. for water testing)
Flip Screen | Switch | ✓ | Flip the topside panel display
Priming | Binary Sensor | ✓ | Priming status
Notification | Binary Sensor | ✓ | Alarm status

## Heat Mode Mapping

The Spa Thermostat climate entity maps spa heat modes to HVAC modes and to a preset, following the same approach as the official Home Assistant Core Balboa integration (`pybalboa`):

| HVAC Mode | Spa Heat Mode | Description |
|-----------|---------------|-------------|
| HEAT | Ready | Actively heating to reach the set point (selectable) |
| OFF | Rest | Heating restricted to filter cycles only (selectable) |
| AUTO | Ready in Rest | Automatic mode, entered by the spa on its own when a pump starts while in Rest mode (display only - selecting it directly is a no-op, there's no command to force it) |

The thermostat entity also exposes a **preset** showing the spa's own heat mode names directly on the card ("Ready" / "Rest" / "Ready in Rest"), settable for Ready/Rest (Ready in Rest is display only, same reasoning as above). There is no separate Heat Mode select entity anymore - this preset replaces it.

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
5. Keep-alive is disabled by default (the spa already pushes status updates on its own); if enabled, sends a heartbeat at the configured interval
6. Process user commands and send appropriate messages with CRC-8 validation

## Entity Statistics

- **Total Sensors:** 14 (Last Known Fault, Heating State, Spa State, Spa Time, WiFi State, Reminder, Sensor A/B Temperature, GFCI Test, Model Name, Software Version, Heater Voltage, Heater Type, Config Signature)
- **Total Binary Sensors:** 5, or 6 if the Circulation Pump binary sensor is detected on your spa
- **Total Switches:** 10 fixed (Blower, Mister, Filter Cycle 2, Hold Mode, Flip Screen, Standby Mode, Reminders, M8 Artificial Intelligence, Panel Lock, Settings Lock) + 1 per detected pump (up to 6) + 1 per detected auxiliary (up to 2), depending on your spa's hardware
- **Total Select Entities:** 4 (Temperature Scale, Clock Mode, Cleanup Cycle, Temperature Range), + 2 Light Color selects instead of Light entities if `light_mode` is `color`
- **Climate Entities:** 1 (Spa Thermostat: HVAC HEAT/OFF/AUTO + preset Ready/Rest/Ready in Rest)
- **Light Entities:** 2 (only when `light_mode` is `switch`, the default)
- **Time Entities:** 4 (Filter Cycle 1/2 Begins/Runs)

## Key Features

### Climate/Thermostat Control
- **HVAC modes:** HEAT (Ready) and OFF (Rest) are selectable; AUTO (Ready in Rest) is shown for display only when the spa enters it on its own
- **Preset:** the spa's own heat mode names ("Ready" / "Rest" / "Ready in Rest") directly on the thermostat card
- **Heating State Monitoring:** Real-time tracking (Off, Heating, Heat Waiting)
- **Temperature Setpoint:** Full control of target water temperature
- **Unit Conversion:** Automatic handling of Fahrenheit/Celsius

### Comprehensive Status Monitoring
- **Spa State Sensor:** Running, Initializing, Hold, or Test mode
- **WiFi State Sensor:** Real-time connection status
- **Temperature Sensors:** Separate sensors for Sensor A and B
- **Last Known Fault:** decoded human-readable fault message, not just a raw code

### Reliability & Protocol Support
- **CRC-8 Validation:** All messages validated with proper checksum
- **Variable Message Lengths:** Support for different spa models
- **Async Socket Communication:** Non-blocking, keep-alive optional (disabled by default) and applied live without needing a reload
- **Automatic Reconnection:** Graceful handling of network interruptions

## Known Limitations

- **`scan_interval` option has no effect.** Every platform file (`sensor.py`, `switch.py`, etc.) hardcodes `SCAN_INTERVAL = timedelta(seconds=1)` at module level, ignoring the configured value entirely - even after a reload. Fixing this properly would need a shared update coordinator or a per-entity override, which is a larger architectural change on its own.
- **Select/preset state values are not translated.** Config flow field labels are translated (en/fr/nb), but the state values themselves (e.g. `Ready`, `Rest`, `Ready in Rest`, `Low`, `High`, `30 min`) are always shown in English, since they are used directly as internal values rather than translation keys. Fixing this for real would mean switching every select/preset to stable snake_case keys (`ready`, `rest`, ...) plus a `state_attributes` translation block per entity, across all select entities consistently - a dedicated iteration on its own.

## Version History

### v0.3.2 (In Development)
- **Objective:** Fix three connection-reliability bugs found while diagnosing recurring disconnections
- **Idle watchdog:** the connection is now considered stale if no data at all has been received from the spa for longer than `socket_timeout`, and a reconnect is forced proactively - instead of only detecting this once the low-level socket `recv()` call itself times out (which could silently take up to the full configured `socket_timeout`, e.g. an hour, to recover)
- **Keep-alive reply verification:** when `keepalive_frame_type` is `existing_client_request`, the integration now actually checks that the WiFi module replies (Module Identification Response) within a short window; if it doesn't, a reconnect is forced instead of assuming the connection is fine just because the TX write succeeded
- **Fixed a leak causing duplicated `sync_time`/option-apply logs:** a failed connection attempt used to register an options-update listener *before* the connection was validated. Since Home Assistant automatically retries a failed setup, every failed attempt left one more listener behind that was never unsubscribed - so a single later options change would fire all of them at once (visible as dozens of duplicate log lines and duplicate `Set Time` commands sent in the same instant). The listener is now only registered after a successful connection
- Removed two unused, dead constants (`SOCKET_TIMEOUT`, `MAX_RETRIES`) left over in `spaclient.py` that were never actually used (the real, configurable timeout is the `self.socket_timeout` instance attribute)

### v0.3.1 (In Development)
- **Objective:** Align the heat mode / HVAC mode mapping with the official Home Assistant Core Balboa integration
- `Rest` now maps to `HVACMode.OFF` instead of `COOL` (a spa never actively cools, so `COOL` was misleading; `OFF` matches `pybalboa`/HA Core's own mapping)
- `Ready in Rest` now maps to `HVACMode.AUTO`. Unlike the official HA Core integration, `AUTO` is kept in `hvac_modes` (not removed) so the thermostat card correctly reflects the state when the spa enters "Ready in Rest" on its own — but it still can't be selected directly (doing so is a no-op, since there's no command to force that state)
- The "Heat Mode" select entity no longer offers "Ready in Rest" as a settable option (it can still be *displayed* when active), fixing a bug where selecting it only sent a blind Ready/Rest toggle instead of actually reaching that state
- `set_heat_mode()` now sends the toggle command twice when transitioning from "Ready in Rest" to "Ready", to reliably land on the requested state (mirrors `pybalboa`'s `HeatModeSpaControl.set_state` logic)
- The thermostat entity now also exposes a **preset** (`ClimateEntityFeature.PRESET_MODE`) showing the spa's own heat mode names directly on the card ("Ready" / "Rest" / "Ready in Rest"), alongside the HVAC mode. The standalone "Heat Mode" select entity has been removed, as it's now redundant with this preset
- The "Temperature Range" switch has been converted to a select entity with two options (`Low` / `High`), for consistency with the other select-based settings
- **Fixed: keep-alive and socket options required a full integration reload to take effect.** `keepalive_enabled`, `keepalive_interval`, `keepalive_frame_type`, and `socket_timeout` are now applied live when options are changed - no reload needed. Also fixed `socket_timeout` never being forwarded to the spa client at all (a pre-existing bug found while investigating this)
- Full README audit: entity tables, Heat Mode Mapping section, and Entity Statistics were still describing the pre-0.3.0/0.3.1 state (old switch-based Temperature Range, old HEAT/COOL/HEAT_COOL mapping, a "Heat Mode" select and a "Circulation Pump Status" switch that no longer/never existed, wrong sensor names). All corrected to match the actual current code.

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
