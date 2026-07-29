# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased] - v0.3.2 (In Development)

**Objective:** Fix three connection-reliability bugs found while diagnosing recurring disconnections.

### Fixed
- **Idle watchdog:** the connection is now considered stale if no data at all has been received from the spa for longer than `socket_timeout`, and a reconnect is forced proactively (checked every second in `keep_alive_call`), instead of only detecting a stale connection once the low-level socket `recv()` call itself times out.
- **Keep-alive reply verification:** when `keepalive_frame_type` is `existing_client_request`, a Module Identification Response is now required within a short window (`min(10s, keepalive_interval)`) after sending the keep-alive frame. If none arrives, a reconnect is forced instead of assuming the connection is fine just because the TX write succeeded.
- **Duplicated `sync_time`/option-apply logs:** a failed connection attempt used to register the options-update listener *before* the connection was validated. Since Home Assistant automatically retries a failed `async_setup_entry`, every failed attempt left one more listener behind, never unsubscribed (unloading never runs for an attempt that never finished setting up). A single later options change would then fire all of them at once. The listener (and `hass.data` entry) is now only registered after a successful connection.

### Removed
- Two unused, dead constants (`SOCKET_TIMEOUT`, `MAX_RETRIES`) in `spaclient.py`, left over from an earlier version and never actually referenced (the real, configurable timeout is the `self.socket_timeout` instance attribute).

## [0.3.1]

**Objective:** Align the heat mode / HVAC mode mapping with the official Home Assistant Core Balboa integration.

### Changed
- `Rest` now maps to `HVACMode.OFF` instead of `COOL` (a spa never actively cools; `OFF` matches `pybalboa`/HA Core's own mapping).
- `Ready in Rest` now maps to `HVACMode.AUTO` (was `HEAT_COOL`). Unlike the official HA Core integration, `AUTO` is kept in `hvac_modes` (now `[HEAT, OFF, AUTO]`) so the thermostat card reflects the state when the spa enters "Ready in Rest" on its own; selecting it directly remains a no-op since there's no command to force that state.
- The "Heat Mode" select entity no longer offers "Ready in Rest" as a settable option, fixing a bug where selecting it only sent a blind Ready/Rest toggle instead of actually reaching that state.
- `set_heat_mode()` now sends the toggle command twice when transitioning from "Ready in Rest" to "Ready", to reliably land on the requested state (mirrors `pybalboa`'s `HeatModeSpaControl.set_state` logic).
- The thermostat entity now also exposes a preset (`ClimateEntityFeature.PRESET_MODE`) showing the spa's own heat mode names directly on the card ("Ready" / "Rest" / "Ready in Rest"), alongside the HVAC mode.
- The "Temperature Range" switch has been converted to a select entity (`Low` / `High`), for consistency with the other select-based settings.

### Removed
- The standalone "Heat Mode" select entity (`select.py`), now redundant with the thermostat's new preset.
- The "Temperature Range" switch entity (`switch.py`), replaced by a select entity.

### Fixed
- Keep-alive and socket options (`keepalive_enabled`, `keepalive_interval`, `keepalive_frame_type`, `socket_timeout`) required a full integration reload to take effect. They are now applied live in `update_listener` when options are changed.
- The keep-alive task used to check `keepalive_enabled` once before entering its loop; if disabled at startup, the task exited and could never be re-enabled without a reload. The check now happens on every loop iteration.
- `socket_timeout` was never forwarded to the spa client constructor at all, so the option had no effect regardless of reload. Now wired in correctly (and applied to the live socket immediately if already connected).

### Known limitation noted
- `scan_interval` still has no effect at all (not just a live-apply issue): every platform hardcodes its own polling interval at module level. Documented in the README as a known limitation for a future iteration.

## [0.3.0]

**Objective:** Rework entities (heat modes, temperature range, LEDs) and adapt the config flow to all current options.

### Added
- `light_mode` option (`switch` | `color`) to choose between simple on/off lights (default, unchanged) and color-cycling selects.
- `BalboaLightSelect` entity: selects a color from a configurable palette by rapidly toggling the light a fixed number of times (reverse-engineered LED cycling behavior).
- Options flow steps to manage the LED palette (add/edit/delete/reset colors) and configure on/off pulse delays plus the cycle-reset delay (seconds, default 3s).

## [0.2.3]

### Added
- Clear separation between normal logs (INFO: connection established, options changed) and debug logs.
- Native debug logging of every outbound command (TX), with name and decoded arguments (e.g. `Toggle Item Command (Pump 2)`), replacing the previous monkey-patch-based logging.
- Debug logging of inbound frames (RX) with de-duplication: the first occurrence of a frame is logged immediately, identical repeats are counted silently, and the count is logged as soon as a different frame arrives.
- Full field-by-field decoding of all known frame types in debug logs (Status Update, Configuration Response, Information Response, Additional Information Response, Preferences Response, Fault Log Response, Filter Cycles Response, GFCI Test Response, Module Identification Response). Unknown frames are logged as raw hex.
- Fault Log Response debug logs now include the decoded human-readable fault message (reusing the existing `FAULT_MSG` table from `const.py`), not just the raw code.
- The two undocumented "?Error?" frame types from the balboa_worldwide_app protocol wiki (0xE1, 0xF0) are now flagged distinctly as `Possible Error Frame (undocumented)` in debug logs instead of blending into generic unknown frames.

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
