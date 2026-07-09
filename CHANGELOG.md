# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased] - v0.2.3 (In Development)

**Objective:** Improve logging to support finer diagnosis of recurring disconnections.

### Added
- Clear separation between normal logs (INFO: connection established, options changed) and debug logs.
- Native debug logging of every outbound command (TX), with name and decoded arguments (e.g. `Toggle Item Command (Pump 2)`), replacing the previous monkey-patch-based logging.
- Debug logging of inbound frames (RX) with de-duplication: the first occurrence of a frame is logged immediately, identical repeats are counted silently, and the count is logged as soon as a different frame arrives.
- Full field-by-field decoding of all known frame types in debug logs (Status Update, Configuration Response, Information Response, Additional Information Response, Preferences Response, Fault Log Response, Filter Cycles Response, GFCI Test Response, Module Identification Response). Unknown frames are logged as raw hex.

### Changed
- Removed the fragile `types.MethodType` monkey-patch previously used in `__init__.py` to capture outbound frames; logging is now built natively into `spaclient.py`.

## [0.2.2]

**Objective:** Make the integration as passive as possible on the connection to improve stability.

### Changed
- Keep-alive is now **disabled by default**. The spa already pushes status updates on its own, so the integration no longer writes to the socket unless the user explicitly opts in via integration options.

### Added
- Configurable **keep-alive frame type** option:
  - `existing_client_request` (default): sends the Existing Client Request frame (`0a bf 04`), which gets a real reply from the WiFi module (Configuration Response) — genuine proof of connection life.
  - `minimal`: sends the previous bare frame (`0a bf 00 00 01`), which the module accepts silently without any reply.
- Missing translations for `keepalive_enabled`, `keepalive_interval`, and `socket_timeout` options (en/fr/nb).

## [0.2.1] - In Development (base)

### Added
- Configurable socket timeout (5-3600s, default: 30s) to handle slow networks.
- Improved connection stability with adjustable timeout settings.

## [0.2.0]

**Objective:** Stabilize connection handling.

### Added
- Configurable keep-alive functionality to prevent module sleep.
- Uses recommended frame: `\x0a\xbf\x00\x00\x01`.
- Keep-alive can be enabled/disabled via integration options.
- Keep-alive interval configurable from 1 to 3600 seconds (1s to 1h).

## [0.1.1]

### Added
- HEAT, COOL, HEAT_COOL mode support to Spa Thermostat climate entity.
- Heat Mode select entity (Ready, Rest, Ready in Rest).

### Removed
- Heat Mode switch entity.

## [0.1.0]

### Changed
- Renamed integration from SmartSpa Client to Balboa Connect.
- Updated all references and documentation.
