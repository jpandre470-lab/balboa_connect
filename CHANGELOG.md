# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased] - v0.3.6 (In Development)

**Objective:** Fix a self-inflicted reconnect loop found by analyzing real logs, plus reduce spurious keep-alive-triggered reconnects.

### Fixed
- Race condition introduced by the 2-worker executor (0.3.5): `_close_socket()` closed/cleared `self.socket_s` unconditionally, regardless of which socket object it actually referred to. If a `recv()` call had been blocked for a long time on an old, already-superseded socket (up to `socket_timeout`), and a *different*, concurrent reconnect attempt succeeded in the meantime, the stale `recv()` finally erroring out would tear down the brand-new connection immediately after it was established (visible in logs as "Reconnected to spa..." instantly followed by "Cannot send message, socket is None"), causing a self-sustaining reconnect loop lasting minutes. `_close_socket()` now accepts an optional `expected_socket` and only actually closes if `self.socket_s` is still that exact object; `read_msg_async()` (the one call site exposed to this race, due to its potentially long-blocking `recv()`) now captures the socket reference before the blocking call and passes it through.
- Spurious keep-alive-triggered reconnects: a keep-alive was only considered acknowledged if the WiFi module specifically replied to the `existing_client_request` frame within the verification window (`_wait_for_keepalive_response`). Confirmed from real logs that the module can be slow/inconsistent about answering this specific query - especially under frequent querying (low `keepalive_missed_updates_threshold`) - while continuing to send its normal spontaneous status broadcasts completely normally. Any new data received after sending the keep-alive now also counts as proof of life, not just the specific reply.
- Description text rendering below (instead of above) every `NumberSelector` field (`sync_time_interval`, `keepalive_missed_updates_threshold`, `fault_log_refresh_interval`, and the 3 LED delay fields). Root cause: HA Core's `ha-selector-number` frontend component hardcodes its helper text to render as a hint below the field in "box" mode - not something overridable from `strings.json`/`data_description`. Worked around with a `ConstantSelector` "note" field (bold, read-only, no input) inserted immediately before each `NumberSelector`, replicating the "paragraph, then compact field" layout `keepalive_frame_type` already gets for free as a radio list.
- Fixed the note text not rendering at all in the first version of the fix above: `ha-selector-constant` doesn't read its text through the normal `strings.json` "data" translation path - it reads a `label` set directly in the selector's own Python-side config, which was left empty. Note text is now picked based on `hass.config.language` (en/fr/nb, falling back to English) and passed as `label` directly.

## [Unreleased] - v0.3.5 (In Development)

**Objective:** Fix a head-of-line blocking bug found while testing 0.3.4's new keep-alive triggers, which made every proactive keep-alive/watchdog mechanism ineffective.

### Fixed
- The socket executor (`ThreadPoolExecutor`) only had 1 worker thread shared between reading (`recv()`, which can legitimately block for the full `socket_timeout` waiting for data) and sending (keep-alive, commands). Any outbound send would queue behind an in-flight `recv()` and only actually execute once that `recv()` timed out on its own. Confirmed from real logs: a keep-alive configured to trigger after ~600ms of silence only actually went out 60 seconds later, at the exact millisecond the low-level socket timeout expired. Now uses 2 worker threads (one for reads, one for writes) - a standard, safe pattern for concurrent socket use.
- Overlapping label/value text on the 3 new `NumberSelector` options added in 0.3.4 (`sync_time_interval`, `keepalive_missed_updates_threshold`, `fault_log_refresh_interval`): labels were still too long to fit above the field on narrow screens, even after the earlier shortening pass. Labels are now minimal, with the full explanation moved to `data_description` (en/fr/nb), matching the pattern already used for `keepalive_frame_type`.

## [Unreleased] - v0.3.4 (In Development)

**Objective:** Configurable time sync and fault log refresh intervals, plus a smarter, dual-trigger keep-alive.

### Added
- Option `sync_time_interval` (1-24h): time sync interval is no longer hardcoded to once a day (86400s).
- Option `fault_log_refresh_interval` (1-24h) and a new periodic background task that re-requests the fault log on this timer, in addition to the existing refresh on reconnect. Previously the fault log was only re-requested at startup and on reconnect, so a new fault raised while the connection stayed up for a long time wasn't picked up promptly.
- Option `keepalive_missed_updates_enabled` + `keepalive_missed_updates_threshold` (1-200): a second, independent keep-alive trigger. The spa spontaneously pushes a status update roughly every ~300ms on its own; if nothing at all has been received for longer than (threshold * ~300ms), a keep-alive is sent right away instead of waiting for the periodic timer. Can be enabled alongside or instead of the existing periodic trigger (`keepalive_enabled`).

### Changed
- `keep_alive_call()`'s watchdog tick tightens to 200ms (from 1s) when `keepalive_missed_updates_enabled` is on, so even a low threshold (down to 1, ~300ms) is detected with reasonable accuracy.

## [0.3.3]

**Objective:** Fix the "nouvel essai: None" message shown in Settings → Devices when the spa is unreachable at startup.

**Note:** an earlier attempt at this version replaced the connection mechanism entirely (removed `ConfigEntryNotReady`, added a custom configurable backoff, entities created immediately as "unavailable"). That approach caused Home Assistant to hang/crash and was reverted. This version starts fresh from 0.3.2 with a minimal, low-risk fix instead.

### Fixed
- Both places that raise `ConfigEntryNotReady` in `__init__.py` now include a descriptive message (e.g. `"Unable to connect to spa at {host}"`), instead of raising it bare. Home Assistant Core stores `str(exception) or None` as the retry reason shown in Settings → Devices; an empty message was literally displayed as the text "None". Confirmed by comparing against the official Home Assistant Core Balboa integration, which always raises `ConfigEntryNotReady` with a message.
- Overlapping label/value text in the LED palette options step (`led_delay_on`/`led_delay_off`/`led_delay_reset`): labels were full sentences that don't shrink to fit above the input field. Shortened to real field names, with the full explanation moved to `data_description` (en/fr/nb).
- The same 3 fields rendered inconsistently (2 as plain text boxes, 1 as a slider with a checkbox) because Home Assistant's form UI defaults small numeric ranges to a slider. All three now use an explicit `NumberSelector` in `box` mode.

### Removed
- The `scan_interval` option (config flow field, `CONFIG_SCHEMA`, options logging). It never had any effect: every platform hardcodes `SCAN_INTERVAL = timedelta(seconds=1)` at module level, ignoring any configured value entirely.

### Not changed
- The reconnection mechanism itself: `ConfigEntryNotReady` is still used, and the retry schedule is still entirely controlled by Home Assistant Core (5s→10→20...capped at 10 minutes). This cannot be customized - `ConfigEntryNotReady` doesn't expose any delay parameter to integrations.

## [0.3.2]

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
