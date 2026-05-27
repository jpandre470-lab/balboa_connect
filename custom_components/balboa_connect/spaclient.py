"""Spa Client integration."""
import asyncio
import concurrent.futures
import homeassistant.util.dt as dt_util
import socket

# Import the device class from the component that you want to support
from .const import _LOGGER
from homeassistant.const import UnitOfTemperature
from homeassistant.util.unit_conversion import TemperatureConverter
from threading import Lock

# Constants for timeouts and retries
# 15s timeout: Balboa sends status every ~1s, so 15s only triggers on real outages
SOCKET_TIMEOUT = 15
REQUEST_TIMEOUT = 30  # Maximum time to wait for a response
MAX_RETRIES = 3
RECONNECT_DELAY = 5


class spaclient:
    def __init__(self, host_ip):
        """ Socket variables """
        self.socket_is_connected = False
        self.socket_l = Lock()
        self.socket_s = None
        self.socket_host_ip = host_ip
        
        """ Task control variables """
        self._stop_flag = False
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1, thread_name_prefix="spa_socket")
        self._loop = None

        """ Status update variable """
        self.status_chunk_array = []

        """ Status update variables """
        self.hold_mode = 0
        self.priming = 0
        self.current_temp = None
        self.hour = 0
        self.minute = 0
        self.heat_mode = "Rest"
        self.hold_mode_remain_time = 0
        self.temp_scale = "Fahrenheit"
        self.filter_mode = False
        self.time_scale = "24 Hr"
        self.heating = False
        self.temp_range = "Low"
        self.pump1 = "Off"
        self.pump2 = "Off"
        self.pump3 = "Off"
        self.pump4 = "Off"
        self.pump5 = "Off"
        self.pump6 = "Off"
        self.circ_pump = False
        self.blower = "Off"
        self.light1 = False
        self.light2 = False
        self.mister = "Off"
        self.aux1 = "Off"
        self.aux2 = "Off"
        self.set_temp = 0
        self.standby_mode = 0
        self.spa_state = 0
        self.reminder_type = 0
        self.sensor_a_temp = None
        self.sensor_b_temp = None
        self.panel_locked = False
        self.settings_locked = False
        self.wifi_state = 0
        self.notification = 0
        self.notification_type = 0
        self.cleanup_cycle_active = 0
        self.sensor_ab_temps = False
        self.m8_cycle_time = 0
        self.flip_screen = 0

        """ Information variables """
        self.info_model_name = "Unknown"
        self.info_cfg_sig = "Unknown"
        self.info_sw_vers = "Unknown"
        self.info_setup = 0
        self.info_ssid = "Unknown"
        self.info_heater_voltage = "Unknown"
        self.info_heater_type = "Unknown"
        self.info_dip_switch = "0000000000000000"
        self.information_loaded = False

        """ Configuration variables """
        self.cfg_pump_array = [0, 0, 0, 0, 0, 0]
        self.cfg_light_array = [0, 0]
        self.cfg_circ_pump_array = [0]
        self.cfg_blower_array = [0]
        self.cfg_mister_array = [0]
        self.cfg_aux_array = [0, 0]
        self.configuration_loaded = False

        """ Module identification variables """
        self.id_macaddr = "Unknown"
        self.id_mac_oui = "Unknown"
        self.id_mac_nic = "Unknown"
        self.module_identification_loaded = False

        """ Filter cycles variables """
        self.filter_1_begins_hour = 0
        self.filter_1_begins_minute = 0
        self.filter_1_runs_hour = 0
        self.filter_1_runs_minute = 0
        self.filter_2_enabled = 0
        self.filter_2_begins_hour = 0
        self.filter_2_begins_minute = 0
        self.filter_2_runs_hour = 0
        self.filter_2_runs_minute = 0
        self.filter_cycles_loaded = False

        """ Additional information variables """
        self.add_info_low_range_min = 0
        self.add_info_low_range_max = 0
        self.add_info_high_range_min = 0
        self.add_info_high_range_max = 0
        self.add_info_nb_of_pumps = 0
        self.additional_information_loaded = False

        """ Preferences variables """
        self.pref_reminder = "Off"
        self.pref_temp_scale = "Fahrenheit"
        self.pref_clock_mode = "24 Hr"
        self.pref_clean_up_cycle = 0
        self.pref_dolphin_address = 0
        self.pref_m8_ai = "Off"
        self.preferences_loaded = False

        """ Fault log variables """
        self.fault_log_total_entries = 0
        self.fault_log_entry_nb = 0
        self.fault_log_msg_code = 0
        self.fault_log_days_ago = 0
        self.fault_log_msg_hour = 0
        self.fault_log_msg_minute = 0
        self.fault_log_todo = 0
        self.fault_log_set_temp = 0
        self.fault_log_sensor_a_temp = 0
        self.fault_log_sensor_b_temp = 0
        self.fault_log_loaded = False

        """ GFCI test variables """
        self.gfci_test_result = 0
        self.gfci_test_loaded = False

    async def get_socket(self):
        """Create and connect socket with proper error handling."""
        if self._loop is None:
            self._loop = asyncio.get_event_loop()
            
        if self.socket_s is not None:
            return True
            
        try:
            self.socket_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket_s.settimeout(SOCKET_TIMEOUT)
            self.socket_s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            
            await self._loop.run_in_executor(
                self._executor,
                lambda: self.socket_s.connect((self.socket_host_ip, 4257))
            )
            _LOGGER.debug("Socket connected to %s:4257", self.socket_host_ip)
            return True
        except (socket.timeout, socket.error, OSError) as e:
            _LOGGER.warning("Socket connection error: %s", e)
            self.socket_is_connected = False
            if self.socket_s:
                try:
                    self.socket_s.close()
                except Exception:
                    pass
            self.socket_s = None
            return False

    async def validate_connection(self):
        """Validate connection with timeout protection."""
        if self._loop is None:
            self._loop = asyncio.get_event_loop()
            
        connected = await self.get_socket()
        if not connected or self.socket_s is None:
            return False

        count = 0
        max_attempts = 50
        
        while count < max_attempts and not self.socket_is_connected and not self._stop_flag:
            try:
                await self.read_msg_async()
            except Exception as e:
                _LOGGER.warning("Error reading message during validation: %s", e)
            await asyncio.sleep(0.1)
            count += 1

        if not self.socket_is_connected:
            _LOGGER.warning("Connection validation failed after %d attempts", count)
            await self._close_socket()

        return self.socket_is_connected
    
    async def _close_socket(self):
        """Safely close the socket."""
        if self.socket_s:
            try:
                self.socket_s.close()
            except Exception:
                pass
            self.socket_s = None
        self.socket_is_connected = False

    async def _reconnect_and_reinit(self):
        """Reconnect socket and send a keep-alive ping to resume spa comms."""
        connected = await self.get_socket()
        if connected:
            _LOGGER.info("Reconnected to spa at %s", self.socket_host_ip)
            await self.send_fault_log_request()
        return connected

    async def keep_alive_call(self):
        """Keep-alive task with proper stop handling."""
        _LOGGER.debug("Keep-alive task started")
        while not self._stop_flag:
            try:
                if self.socket_s is None:
                    _LOGGER.debug("Keep-alive: socket is None, backup reconnect attempt")
                    connected = await self._reconnect_and_reinit()
                    if not connected:
                        _LOGGER.warning("Keep-alive: reconnection failed, will retry")
                        await asyncio.sleep(RECONNECT_DELAY)
                        continue
                else:
                    await self.send_fault_log_request()
            except asyncio.CancelledError:
                _LOGGER.debug("Keep-alive task cancelled")
                break
            except Exception as e:
                _LOGGER.error("Error in keep_alive_call: %s", e)
                await self._close_socket()
            await asyncio.sleep(30)
        _LOGGER.debug("Keep-alive task stopped")

    def compute_checksum(self, length, payload):
        crc = 0xb5
        for cur in range(length):
            for i in range(8):
                bit = crc & 0x80
                crc = ((crc << 1) & 0xff) | ((payload[cur] >> (7 - i)) & 0x01)
                if bit:
                    crc = crc ^ 0x07
            crc &= 0xff
        for i in range(8):
            bit = crc & 0x80
            crc = (crc << 1) & 0xff
            if bit:
                crc ^= 0x07
        return crc ^ 0x02

    def _read_msg_sync(self):
        """Synchronous message read - runs in executor thread."""
        if self.socket_s is None:
            return None
            
        try:
            len_chunk = self.socket_s.recv(2)
        except (socket.timeout, socket.error, OSError) as e:
            _LOGGER.debug("Socket recv(2) error: %s", e)
            return None

        if len_chunk == b'~' or len_chunk == b'' or len(len_chunk) == 0:
            return b''

        if len(len_chunk) < 2:
            return b''
            
        length = len_chunk[1]

        if int(length) == 0:
            return b''

        try:
            chunk = self.socket_s.recv(length)
        except (socket.timeout, socket.error, OSError) as e:
            _LOGGER.debug("Socket recv(length) error: %s", e)
            return None

        return chunk
    
    async def read_msg_async(self):
        """Async wrapper for message reading - doesn't block event loop."""
        if self._loop is None:
            self._loop = asyncio.get_event_loop()
            
        if self.socket_s is None:
            return False
            
        self.socket_l.acquire()
        try:
            chunk = await self._loop.run_in_executor(self._executor, self._read_msg_sync)
        except Exception as e:
            _LOGGER.debug("Error in read_msg_async executor: %s", e)
            chunk = None
        finally:
            self.socket_l.release()
        
        if chunk is None:
            self.socket_is_connected = False
            await self._close_socket()
            return False
            
        if chunk == b'':
            return True
            
        return self._process_chunk(chunk)
    
    def read_msg(self):
        """Legacy sync read_msg for backward compatibility - USE read_msg_async INSTEAD."""
        if self.socket_s is None:
            return False
            
        self.socket_l.acquire()

        try:
            len_chunk = self.socket_s.recv(2)
        except (socket.timeout, socket.error, OSError) as e:
            _LOGGER.debug("Socket recv(2) error: %s", e)
            self.socket_is_connected = False
            self.socket_l.release()
            try:
                self.socket_s.close()
            except Exception:
                pass
            self.socket_s = None
            return False

        if len_chunk == b'~' or len_chunk == b'' or len(len_chunk) == 0:
            self.socket_l.release()
            return True

        if len(len_chunk) < 2:
            self.socket_l.release()
            return True
            
        length = len_chunk[1]

        if int(length) == 0:
            self.socket_l.release()
            return True

        try:
            chunk = self.socket_s.recv(length)
        except (socket.timeout, socket.error, OSError) as e:
            _LOGGER.debug("Socket recv(length) error: %s", e)
            self.socket_is_connected = False
            self.socket_l.release()
            try:
                self.socket_s.close()
            except Exception:
                pass
            self.socket_s = None
            return False

        self.socket_l.release()
        return self._process_chunk(chunk)
    
    def _process_chunk(self, chunk):
        """Process received chunk and parse response."""
        if chunk is None or len(chunk) < 3:
            return True
            
        if chunk != self.status_chunk_array:
            if chunk[0:3] == b'\xff\xaf\x13' and ((self.information_loaded and self.additional_information_loaded and self.preferences_loaded and self.configuration_loaded and self.module_identification_loaded) or (self.socket_is_connected == False)):
                try:
                    self.parse_status_update(chunk[3:])
                    self.status_chunk_array = chunk
                    self.socket_is_connected = True
                except Exception as e:
                    _LOGGER.warning("Error parsing status update: %s", e)
                return True

            if chunk[0:3] == b'\x0a\xbf\x23':
                try:
                    self.parse_filter_cycles_response(chunk[3:])
                except Exception as e:
                    _LOGGER.warning("Error parsing filter cycles: %s", e)
                return True

            if chunk[0:3] == b'\x0a\xbf\x24' and self.information_loaded != True:
                try:
                    self.parse_information_response(chunk[3:])
                except Exception as e:
                    _LOGGER.warning("Error parsing information: %s", e)
                return True

            if chunk[0:3] == b'\x0a\xbf\x25' and self.additional_information_loaded != True:
                try:
                    self.parse_additional_information_response(chunk[3:])
                except Exception as e:
                    _LOGGER.warning("Error parsing additional information: %s", e)
                return True

            if chunk[0:3] == b'\x0a\xbf\x26' and self.preferences_loaded != True:
                try:
                    self.parse_preferences_response(chunk[3:])
                except Exception as e:
                    _LOGGER.warning("Error parsing preferences: %s", e)
                return True

            if chunk[0:3] == b'\x0a\xbf\x28':
                try:
                    self.parse_fault_log_response(chunk[3:])
                except Exception as e:
                    _LOGGER.warning("Error parsing fault log: %s", e)
                return True

            if chunk[0:3] == b'\x0a\xbf\x2b':
                try:
                    self.parse_gfci_test_response(chunk[3:])
                except Exception as e:
                    _LOGGER.warning("Error parsing GFCI test: %s", e)
                return True

            if chunk[0:3] == b'\x0a\xbf\x2e' and self.configuration_loaded != True:
                try:
                    self.parse_configuration_response(chunk[3:])
                except Exception as e:
                    _LOGGER.warning("Error parsing configuration: %s", e)
                return True

            if chunk[0:3] == b'\x0a\xbf\x94' and self.module_identification_loaded != True:
                try:
                    self.parse_module_identification_response(chunk[3:])
                except Exception as e:
                    _LOGGER.warning("Error parsing module identification: %s", e)
                return True

        return True

    async def read_all_msg(self):
        """Main message reading loop with proper stop handling."""
        _LOGGER.debug("Message reading task started")
        _next_reconnect_at = None
        while not self._stop_flag:
            try:
                if self.socket_s is not None:
                    _next_reconnect_at = None
                    await self.read_msg_async()
                    await asyncio.sleep(0.1)
                else:
                    now = asyncio.get_event_loop().time()
                    if _next_reconnect_at is None:
                        _next_reconnect_at = now + RECONNECT_DELAY
                        _LOGGER.warning("Socket lost, will attempt reconnect in %ds", RECONNECT_DELAY)
                    elif now >= _next_reconnect_at:
                        _LOGGER.info("read_all_msg: attempting reconnect")
                        connected = await self._reconnect_and_reinit()
                        if connected:
                            _next_reconnect_at = None
                        else:
                            _next_reconnect_at = asyncio.get_event_loop().time() + RECONNECT_DELAY
                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                _LOGGER.debug("Message reading task cancelled")
                break
            except Exception as e:
                _LOGGER.error("Error in read_all_msg: %s", e)
                await asyncio.sleep(0.1)
        _LOGGER.debug("Message reading task stopped")
    
    async def stop(self):
        """Stop all background tasks and close connections."""
        _LOGGER.info("Stopping spa client")
        self._stop_flag = True
        await self._close_socket()
        if self._executor:
            self._executor.shutdown(wait=False)
        _LOGGER.info("Spa client stopped")