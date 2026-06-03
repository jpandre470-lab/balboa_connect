# Changelog - balboa_connect

All notable changes to the Balboa Connect Home Assistant integration are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.2.4] - 2026-06-02

### Changed
- **Configurable socket timeout**: Socket timeout is now configurable via integration options (1-3600 seconds)
- **Added min/max descriptions to option fields**: Each option field now displays its valid range in the description
- Removed `CONF_SCAN_INTERVAL` configuration option (was non-functional - entities update via real-time spa status messages, not polling)
- Time synchronization enabled by default
- Added configurable time synchronization interval (1-24 hours, default: 1 hour) with select dropdown

### Technical Details
- **const.py**: Added `CONF_SOCKET_TIMEOUT`, `DEFAULT_SOCKET_TIMEOUT=15`, `MIN_SOCKET_TIMEOUT=1`, `MAX_SOCKET_TIMEOUT=3600`
- **const.py**: Added interval min/max constants for all configurable intervals
- **spaclient.py**: Modified `__init__()` to accept `socket_timeout` parameter (default: 15)
- **spaclient.py**: Removed hardcoded `SOCKET_TIMEOUT` constant, now uses `self.socket_timeout`
- **spaclient.py**: Updated `get_socket()` to use `self.socket_timeout` for `settimeout()`
- **__init__.py**: Modified to read `CONF_SOCKET_TIMEOUT` from options and pass to spaclient
- **__init__.py**: Added socket timeout handling in `update_listener()` to recreate spa client when timeout changes
- **config_flow.py**: Updated to expose new options with min/max descriptions

---

## [0.2.3] - 2026-06-02

### Changed
- **Configurable fault log**: Fault log requests can now be enabled/disabled and have configurable interval (1-24 hours, default: 6 hours)
- Removed `CONF_SCAN_INTERVAL` configuration option (non-functional)
- Time synchronization enabled by default
- Added configurable time synchronization interval with select dropdown

### Technical Details
- **const.py**: Added `CONF_FAULT_LOG_ENABLED`, `CONF_FAULT_LOG_INTERVAL`, `DEFAULT_FAULT_LOG_INTERVAL=6`, `MIN_FAULT_LOG_INTERVAL=1`, `MAX_FAULT_LOG_INTERVAL=24`
- **__init__.py**: Added `DATA_FAULT_LOG_TASK` constant
- **__init__.py**: Added fault log configuration to `CONFIG_SCHEMA`
- **__init__.py**: Added fault log task creation in `async_setup_entry()`
- **__init__.py**: Added fault log task management in `async_unload_entry()`
- **__init__.py**: Added fault log task handling in `update_listener()` with enable/disable and interval configuration
- **config_flow.py**: Added fault log options with select dropdown fields
- **config_flow.py**: Changed `CONF_SYNC_TIME` default to `True`
- **config_flow.py**: Added `CONF_SYNC_TIME_INTERVAL` with select dropdown

---

## [0.2.2] - 2026-06-02

### Removed
- **Complete removal of keep-alive mechanism**: The keep_alive_call method and all related functionality has been removed to implement a truly passive protocol.

### Changed
- Removed `CONF_SCAN_INTERVAL` configuration option (non-functional)
- Time synchronization enabled by default
- Added configurable time synchronization interval with select dropdown

### Technical Details
- **spaclient.py**: Removed `keep_alive_call()` method entirely
- **spaclient.py**: Removed related comment in `read_all_msg()` referencing keep_alive
- **__init__.py**: Removed `DATA_KEEP_ALIVE_TASK` constant
- **__init__.py**: Removed `DATA_KEEP_ALIVE_TASK` from entry data initialization
- **__init__.py**: Removed keep_alive task management from `async_unload_entry()`
- **const.py**: Added time synchronization interval constants
- **__init__.py**: Updated to use new constants
- **config_flow.py**: Updated to expose new options

---

## [0.2.1] - 2026-06-01

### Base Version
- Stable version with keep_alive mechanism
- Two existing configuration options:
  - Entity refresh interval (set to 1s by default, but non-functional)
  - Time synchronization with Home Assistant (disabled by default)
- Entities update in real-time via spa status messages (every ~1 second)
- Uses single ThreadPoolExecutor for all socket operations
- Socket timeout hardcoded to 15 seconds

---

## [0.2.0] - 2026-05-XX

### Initial Fork
- Forked from upstream smartspaclient repository
- Initial implementation of Balboa Connect integration for Home Assistant

---

## [0.1.0] - 2026-05-XX

### Initial Release
- First version of the Balboa Connect integration
