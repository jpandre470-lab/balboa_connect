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
        """Async wrapper for message reading."""
        if self._loop is None:
            self._loop = asyncio.get_event_loop()
            
        if self.socket_s is None:
            return False
            
        self.socket_l.acquire()
        try:
            chunk = await self._loop.run_in_executor(self._executor, self._read_msg_sync)
        except Exception as e:
            _LOGGER.debug("Error in read_msg_async: %s", e)
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
        """Legacy sync read_msg - USE read_msg_async INSTEAD."""
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
        """Main message reading loop."""
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
        """Stop all background tasks."""
        _LOGGER.info("Stopping spa client")
        self._stop_flag = True
        await self._close_socket()
        if self._executor:
            self._executor.shutdown(wait=False)
        _LOGGER.info("Spa client stopped")

    def parse_additional_information_response(self, byte_array):
        """Parse additional information response."""
        self.add_info_low_range_min = byte_array[2]
        self.add_info_low_range_max = byte_array[3]
        self.add_info_high_range_min = byte_array[4]
        self.add_info_high_range_max = byte_array[5]
        self.add_info_nb_of_pumps = (
            (byte_array[7] & 0x01) + (byte_array[7] >> 1 & 0x01) +
            (byte_array[7] >> 2 & 0x01) + (byte_array[7] >> 3 & 0x01) +
            (byte_array[7] >> 4 & 0x01) + (byte_array[7] >> 5 & 0x01))
        self.additional_information_loaded = True

    def parse_configuration_response(self, byte_array):
        """Parse configuration response."""
        self.cfg_pump_array[0] = int((byte_array[0] & 0x03))
        self.cfg_pump_array[1] = int((byte_array[0] & 0x0c) >> 2)
        self.cfg_pump_array[2] = int((byte_array[0] & 0x30) >> 4)
        self.cfg_pump_array[3] = int((byte_array[0] & 0xc0) >> 6)
        self.cfg_pump_array[4] = int((byte_array[1] & 0x03))
        self.cfg_pump_array[5] = int((byte_array[1] & 0xc0) >> 6)
        self.cfg_light_array[0] = int((byte_array[2] & 0x03) != 0)
        self.cfg_light_array[1] = int((byte_array[2] & 0xc0) != 0)
        self.cfg_circ_pump_array[0] = int((byte_array[3] & 0x80) != 0)
        self.cfg_blower_array[0] = int((byte_array[3] & 0x03) != 0)
        self.cfg_mister_array[0] = int((byte_array[4] & 0x30) != 0)
        self.cfg_aux_array[0] = int((byte_array[4] & 0x01) != 0)
        self.cfg_aux_array[1] = int((byte_array[4] & 0x02) != 0)
        self.configuration_loaded = True

    def parse_fault_log_response(self, byte_array):
        """Parse fault log response."""
        self.fault_log_total_entries = byte_array[0]
        self.fault_log_entry_nb = byte_array[1]
        self.fault_log_msg_code = byte_array[2]
        self.fault_log_days_ago = byte_array[3]
        self.fault_log_msg_hour = byte_array[4]
        self.fault_log_msg_minute = byte_array[5]
        self.fault_log_todo = byte_array[6]
        self.fault_log_set_temp = byte_array[7]
        self.fault_log_sensor_a_temp = byte_array[8]
        self.fault_log_sensor_b_temp = byte_array[9]
        self.fault_log_loaded = True

    def parse_filter_cycles_response(self, byte_array):
        """Parse filter cycles response."""
        self.filter_1_begins_hour = byte_array[0]
        self.filter_1_begins_minute = byte_array[1]
        self.filter_1_runs_hour = byte_array[2]
        self.filter_1_runs_minute = byte_array[3]
        self.filter_2_enabled = byte_array[4] >> 7
        self.filter_2_begins_hour = byte_array[4] ^ (self.filter_2_enabled << 7)
        self.filter_2_begins_minute = byte_array[5]
        self.filter_2_runs_hour = byte_array[6]
        self.filter_2_runs_minute = byte_array[7]
        self.filter_cycles_loaded = True

    def parse_gfci_test_response(self, byte_array):
        """Parse GFCI test response."""
        self.gfci_test_result = byte_array[0]
        self.gfci_test_loaded = True

    def parse_information_response(self, byte_array):
        """Parse information response."""
        model = [byte_array[4], byte_array[5], byte_array[6], byte_array[7],
                 byte_array[8], byte_array[9], byte_array[10], byte_array[11]]
        self.info_model_name = "".join(map(chr, model)).strip()
        self.info_sw_vers = f"{byte_array[2]}.{byte_array[3]}"
        self.info_setup = byte_array[12]
        self.info_ssid = f"M{byte_array[0]}_{byte_array[1]} V{self.info_sw_vers}"
        self.info_cfg_sig = f"{byte_array[13]:x}{byte_array[14]:x}{byte_array[15]:x}{byte_array[16]:x}"
        self.info_heater_voltage = 240 if byte_array[17] == 0x01 else "Unknown"
        self.info_heater_type = "Standard" if byte_array[18] == 0x0A else "Unknown"
        self.info_dip_switch = f"{byte_array[19]:08b}{byte_array[20]:08b}"
        self.information_loaded = True

    def parse_module_identification_response(self, byte_array):
        """Parse module identification response."""
        self.id_macaddr = f"{byte_array[3]:02x}:{byte_array[4]:02x}:{byte_array[5]:02x}:"
                       f"{byte_array[6]:02x}:{byte_array[7]:02x}:{byte_array[8]:02x}"
        self.id_mac_oui = f"{byte_array[17]:02x}:{byte_array[18]:02x}:{byte_array[19]:02x}"
        self.id_mac_nic = f"{byte_array[22]:02x}:{byte_array[23]:02x}:{byte_array[24]:02x}"
        self.module_identification_loaded = True

    def parse_preferences_response(self, byte_array):
        """Parse preferences response."""
        self.pref_reminder = ("Off", "On")[byte_array[1] & 0x01]
        self.pref_temp_scale = ("Fahrenheit", "Celsius")[byte_array[3] & 0x01]
        self.pref_clock_mode = ("12 Hr", "24 Hr")[byte_array[4] & 0x01]
        self.pref_clean_up_cycle = byte_array[5]
        self.pref_dolphin_address = byte_array[6]
        self.pref_m8_ai = ("Off", "On")[byte_array[8] & 0x01]
        self.preferences_loaded = True

    def parse_status_update(self, byte_array):
        """Parse a status update from the spa."""
        self.hold_mode = 1 if byte_array[0] == 0x05 else 0
        self.priming = 1 if byte_array[1] == 0x01 else 0
        self.current_temp = byte_array[2] if (byte_array[2] != 255) else None
        self.hour = byte_array[3]
        self.minute = byte_array[4]
        self.heat_mode = ("Ready", "Rest", "Ready in Rest")[byte_array[5] & 0x03]
        self.reminder_type = byte_array[6]
        self.sensor_a_temp = byte_array[7] if (byte_array[7] != 255) else None
        self.sensor_b_temp = byte_array[8] if (byte_array[8] != 255) else None
        self.temp_scale = ("Fahrenheit", "Celsius")[byte_array[9] & 0x01]
        self.time_scale = ("12 Hr", "24 Hr")[byte_array[9] >> 1 & 0x01]
        self.filter_mode = byte_array[9] >> 2 & 0x03
        self.heating = byte_array[10] >> 4 & 0x03
        self.temp_range = ("Low", "High")[byte_array[10] >> 2 & 0x01]
        self.pump1 = ("Off", "Low", "High")[byte_array[11] & 0x03]
        self.pump2 = ("Off", "Low", "High")[(byte_array[11] >> 2) & 0x03]
        self.pump3 = ("Off", "Low", "High")[(byte_array[11] >> 4) & 0x03]
        self.pump4 = ("Off", "Low", "High")[(byte_array[11] >> 6) & 0x03]
        self.pump5 = ("Off", "Low", "High")[byte_array[12] & 0x03]
        self.pump6 = ("Off", "Low", "High")[(byte_array[12] >> 6) & 0x03]
        self.circ_pump = (byte_array[13] & 0x02) != 0
        self.blower = ("Off", "On")[(byte_array[13] & 0x0C) != 0]
        self.light1 = (byte_array[14] & 0x03) == 0x03
        self.light2 = (byte_array[14] & 0xC0) == 0xC0
        self.mister = ("Off", "On")[byte_array[15] & 0x01]
        self.aux1 = ("Off", "On")[(byte_array[15] & 0x08) != 0]
        self.aux2 = ("Off", "On")[(byte_array[15] & 0x10) != 0]
        self.set_temp = byte_array[19]
        self.standby_mode = 1 if byte_array[22] == 0x40 else 0
        self.spa_state = byte_array[22]
        self.notification = 1 if (byte_array[17] & 0x20) else 0
        self.notification_type = byte_array[18]
        self.cleanup_cycle_active = 1 if (byte_array[16] & 0x04) else 0
        self.sensor_ab_temps = 1 if (byte_array[18] & 0x02) else 0
        self.m8_cycle_time = byte_array[24] * 30 if byte_array[24] in [1, 2, 3, 4] else 0
        self.flip_screen = byte_array[23]
        self.socket_is_connected = True

    # Request methods
    def send_fault_log_request(self):
        payload = bytearray([0x0a, 0xbf, 0x28, 0x00])
        payload[3] = self.compute_checksum(3, payload)
        self._send_message(payload)

    def send_configuration_request(self):
        payload = bytearray([0x0a, 0xbf, 0x2e, 0x00])
        payload[3] = self.compute_checksum(3, payload)
        self._send_message(payload)

    def send_filter_cycles_request(self):
        payload = bytearray([0x0a, 0xbf, 0x23, 0x00])
        payload[3] = self.compute_checksum(3, payload)
        self._send_message(payload)

    def send_gfci_test_request(self):
        payload = bytearray([0x0a, 0xbf, 0x2b, 0x00])
        payload[3] = self.compute_checksum(3, payload)
        self._send_message(payload)

    def send_information_request(self):
        payload = bytearray([0x0a, 0xbf, 0x24, 0x00])
        payload[3] = self.compute_checksum(3, payload)
        self._send_message(payload)

    def send_preferences_request(self):
        payload = bytearray([0x0a, 0xbf, 0x26, 0x00])
        payload[3] = self.compute_checksum(3, payload)
        self._send_message(payload)

    def send_module_identification_request(self):
        payload = bytearray([0x0a, 0xbf, 0x94, 0x00])
        payload[3] = self.compute_checksum(3, payload)
        self._send_message(payload)

    def send_additional_information_request(self):
        payload = bytearray([0x0a, 0xbf, 0x25, 0x00])
        payload[3] = self.compute_checksum(3, payload)
        self._send_message(payload)

    def _send_message(self, payload):
        if self.socket_s is None:
            return
        message = bytearray([0x7E, len(payload), 0x00]) + payload + bytearray([0x7E])
        try:
            self.socket_s.sendall(message)
        except Exception as e:
            _LOGGER.warning("Error sending message: %s", e)

    def print_variables(self):
        """Print all variables for debugging."""
        _LOGGER.debug("=== Spa Client Variables ===")
        _LOGGER.debug(f"Hold Mode: {self.hold_mode}")
        _LOGGER.debug(f"Priming: {self.priming}")
        _LOGGER.debug(f"Current Temp: {self.current_temp}")
        _LOGGER.debug(f"Hour: {self.hour}")
        _LOGGER.debug(f"Minute: {self.minute}")
        _LOGGER.debug(f"Heat Mode: {self.heat_mode}")
        _LOGGER.debug(f"Temp Scale: {self.temp_scale}")
        _LOGGER.debug(f"Time Scale: {self.time_scale}")
        _LOGGER.debug(f"Heating: {self.heating}")
        _LOGGER.debug(f"Temp Range: {self.temp_range}")
        for i in range(1, 7):
            _LOGGER.debug(f"Pump {i}: {getattr(self, f'pump{i}')}")
        _LOGGER.debug(f"Circ Pump: {self.circ_pump}")
        _LOGGER.debug(f"Blower: {self.blower}")
        _LOGGER.debug(f"Light 1: {self.light1}")
        _LOGGER.debug(f"Light 2: {self.light2}")
        _LOGGER.debug(f"Mister: {self.mister}")
        _LOGGER.debug(f"Aux 1: {self.aux1}")
        _LOGGER.debug(f"Aux 2: {self.aux2}")
        _LOGGER.debug(f"Set Temp: {self.set_temp}")
        _LOGGER.debug(f"Standby Mode: {self.standby_mode}")
        _LOGGER.debug(f"Spa State: {self.spa_state}")
        _LOGGER.debug(f"Sensor A Temp: {self.sensor_a_temp}")
        _LOGGER.debug(f"Sensor B Temp: {self.sensor_b_temp}")
        _LOGGER.debug(f"Panel Locked: {self.panel_locked}")
        _LOGGER.debug(f"Settings Locked: {self.settings_locked}")
        _LOGGER.debug(f"WiFi State: {self.wifi_state}")
        _LOGGER.debug(f"Notification: {self.notification}")
        _LOGGER.debug(f"Notification Type: {self.notification_type}")
        _LOGGER.debug(f"Filter Mode: {self.filter_mode}")
        _LOGGER.debug(f"M8 Cycle Time: {self.m8_cycle_time}")
        _LOGGER.debug(f"Flip Screen: {self.flip_screen}")

    # Getter methods
    def get_hold_mode(self):
        return self.hold_mode

    def get_priming(self):
        return self.priming

    def get_current_temp(self):
        return self.current_temp

    def get_hour(self):
        return self.hour

    def get_minute(self):
        return self.minute

    def get_heat_mode(self):
        return self.heat_mode

    def get_hold_mode_remain_time(self):
        return self.hold_mode_remain_time

    def get_temp_scale(self):
        return self.temp_scale

    def get_filter_mode(self, filter_num):
        if filter_num == 1:
            return self.filter_mode == 1 or self.filter_mode == 3
        elif filter_num == 2:
            return self.filter_mode == 2 or self.filter_mode == 3
        return False

    def get_filter_begins(self, filter_num):
        if filter_num == 1:
            return f"{self.filter_1_begins_hour:02d}:{self.filter_1_begins_minute:02d}"
        elif filter_num == 2:
            return f"{self.filter_2_begins_hour:02d}:{self.filter_2_begins_minute:02d}"
        return "N/A"

    def get_filter_runs(self, filter_num):
        if filter_num == 1:
            return f"{self.filter_1_runs_hour:02d}:{self.filter_1_runs_minute:02d}"
        elif filter_num == 2:
            return f"{self.filter_2_runs_hour:02d}:{self.filter_2_runs_minute:02d}"
        return "N/A"

    def get_filter_ends(self, filter_num):
        if filter_num == 1:
            end_hour = (self.filter_1_begins_hour + self.filter_1_runs_hour) % 24
            end_minute = (self.filter_1_begins_minute + self.filter_1_runs_minute) % 60
            return f"{end_hour:02d}:{end_minute:02d}"
        elif filter_num == 2:
            end_hour = (self.filter_2_begins_hour + self.filter_2_runs_hour) % 24
            end_minute = (self.filter_2_begins_minute + self.filter_2_runs_minute) % 60
            return f"{end_hour:02d}:{end_minute:02d}"
        return "N/A"

    def get_time_scale(self):
        return self.time_scale

    def get_heating(self):
        return self.heating

    def get_heating_state(self):
        if self.heating == 0:
            return "Off"
        elif self.heating == 1:
            return "Heating"
        elif self.heating == 2:
            return "Heat Waiting"
        return "Unknown"

    def get_temp_range(self):
        return self.temp_range

    def get_pump(self, pump_num):
        return getattr(self, f'pump{pump_num}')

    def get_pump_list(self):
        return self.cfg_pump_array

    def get_circ_pump(self):
        return self.circ_pump

    def get_circ_pump_list(self):
        return self.cfg_circ_pump_array

    def get_blower(self):
        return self.blower

    def get_blower_list(self):
        return self.cfg_blower_array

    def get_light(self, light_num):
        return getattr(self, f'light{light_num}')

    def get_light_list(self):
        return self.cfg_light_array

    def get_mister(self):
        return self.mister

    def get_mister_list(self):
        return self.cfg_mister_array

    def get_aux(self, aux_num):
        return getattr(self, f'aux{aux_num}')

    def get_aux_list(self):
        return self.cfg_aux_array

    def get_standby_mode(self):
        return self.standby_mode

    def get_spa_state(self):
        if self.spa_state == 0x00:
            return "Running"
        elif self.spa_state == 0x01:
            return "Initializing"
        elif self.spa_state == 0x05:
            return "Hold Mode"
        elif self.spa_state == 0x17:
            return "Test Mode"
        return "Unknown"

    def get_reminder_type(self):
        return self.reminder_type

    def get_reminder_type_text(self):
        if self.reminder_type == 0x00:
            return "None"
        elif self.reminder_type == 0x04:
            return "Clean Filter"
        elif self.reminder_type == 0x0A:
            return "Check pH"
        elif self.reminder_type == 0x09:
            return "Check Sanitizer"
        elif self.reminder_type == 0x1E:
            return "Fault"
        return "Unknown"

    def get_sensor_a_temp(self):
        return self.sensor_a_temp

    def get_sensor_b_temp(self):
        return self.sensor_b_temp

    def get_panel_locked(self):
        return self.panel_locked

    def get_settings_locked(self):
        return self.settings_locked

    def get_wifi_state(self):
        return self.wifi_state

    def get_wifi_state_text(self):
        if self.wifi_state == 0:
            return "Connected"
        elif self.wifi_state == 1:
            return "Connecting"
        return "Not Connected"

    def get_notification(self):
        return self.notification

    def get_notification_type(self):
        return self.notification_type

    def get_cleanup_cycle_active(self):
        return self.cleanup_cycle_active

    def get_sensor_ab_temps(self):
        return self.sensor_ab_temps

    def get_m8_cycle_time(self):
        return self.m8_cycle_time

    def get_flip_screen(self):
        return self.flip_screen

    def get_gateway_status(self):
        return self.socket_is_connected

    def get_macaddr(self):
        return self.id_macaddr

    def get_model_name(self):
        return self.info_model_name

    def get_ssid(self):
        return self.info_ssid

    def get_info_heater_voltage(self):
        return self.info_heater_voltage

    def get_info_heater_type(self):
        return self.info_heater_type

    def get_info_cfg_sig(self):
        return self.info_cfg_sig

    def get_fault_log_msg_code(self):
        return self.fault_log_msg_code

    def get_filter2_enabled(self):
        return self.filter_2_enabled

    # Setter methods
    async def set_temperature(self, temp):
        payload = bytearray([0x0a, 0xbf, 0x11, 0x00, 0x00, temp, 0x00])
        payload[3] = self.compute_checksum(3, payload)
        self._send_message(payload)

    def set_pump(self, pump_num, state):
        pump_states = {"Off": 0x00, "Low": 0x01, "High": 0x02}
        state_value = pump_states.get(state, 0x00)
        payload = bytearray([0x0a, 0xbf, 0x11, 0x00, pump_num - 1, state_value, 0x00])
        payload[3] = self.compute_checksum(3, payload)
        self._send_message(payload)

    def set_light(self, light_num, state):
        state_value = 0x01 if state else 0x00
        payload = bytearray([0x0a, 0xbf, 0x11, 0x00, 0x06 + light_num - 1, state_value, 0x00])
        payload[3] = self.compute_checksum(3, payload)
        self._send_message(payload)

    def set_blower(self, state):
        state_value = 0x01 if state == "On" else 0x00
        payload = bytearray([0x0a, 0xbf, 0x11, 0x00, 0x08, state_value, 0x00])
        payload[3] = self.compute_checksum(3, payload)
        self._send_message(payload)

    def set_mister(self, state):
        state_value = 0x01 if state == "On" else 0x00
        payload = bytearray([0x0a, 0xbf, 0x11, 0x00, 0x09, state_value, 0x00])
        payload[3] = self.compute_checksum(3, payload)
        self._send_message(payload)

    def set_aux(self, aux_num, state):
        state_value = 0x01 if state == "On" else 0x00
        aux_pos = 0x0A if aux_num == 1 else 0x0B
        payload = bytearray([0x0a, 0xbf, 0x11, 0x00, aux_pos, state_value, 0x00])
        payload[3] = self.compute_checksum(3, payload)
        self._send_message(payload)

    def set_heat_mode(self, mode):
        mode_value = 0x01 if mode == "Ready" else 0x00
        payload = bytearray([0x0a, 0xbf, 0x27, 0x01, mode_value, 0x00])
        payload[3] = self.compute_checksum(3, payload)
        self._send_message(payload)

    def set_standby_mode(self):
        payload = bytearray([0x0a, 0xbf, 0x1d, 0x00, 0x00])
        payload[3] = self.compute_checksum(3, payload)
        self._send_message(payload)

    def set_temp_range(self, range_value):
        range_map = {"Low": 0x00, "High": 0x01}
        range_value = range_map.get(range_value, 0x00)
        payload = bytearray([0x0a, 0xbf, 0x27, 0x04, range_value, 0x00])
        payload[3] = self.compute_checksum(3, payload)
        self._send_message(payload)

    def set_temperature_scale(self, scale):
        scale_value = 0x01 if scale == "Celsius" else 0x00
        payload = bytearray([0x0a, 0xbf, 0x27, 0x03, scale_value, 0x00])
        payload[3] = self.compute_checksum(3, payload)
        self._send_message(payload)

    def set_clock_mode(self, mode):
        mode_value = 0x01 if mode == "24 Hr" else 0x00
        payload = bytearray([0x0a, 0xbf, 0x27, 0x02, mode_value, 0x00])
        payload[3] = self.compute_checksum(3, payload)
        self._send_message(payload)

    def set_cleanup_cycle(self, value):
        payload = bytearray([0x0a, 0xbf, 0x27, 0x05, value, 0x00])
        payload[3] = self.compute_checksum(3, payload)
        self._send_message(payload)

    def set_reminders(self, enabled):
        value = 0x01 if enabled else 0x00
        payload = bytearray([0x0a, 0xbf, 0x27, 0x01, value, 0x00])
        payload[3] = self.compute_checksum(3, payload)
        self._send_message(payload)

    def set_m8_ai(self, enabled):
        value = 0x01 if enabled else 0x00
        payload = bytearray([0x0a, 0xbf, 0x27, 0x08, value, 0x00])
        payload[3] = self.compute_checksum(3, payload)
        self._send_message(payload)

    def set_panel_lock(self, locked):
        value = 0x01 if locked else 0x00
        payload = bytearray([0x0a, 0xbf, 0x2d, 0x01, value, 0x00])
        payload[3] = self.compute_checksum(3, payload)
        self._send_message(payload)

    def set_settings_lock(self, locked):
        value = 0x01 if locked else 0x00
        payload = bytearray([0x0a, 0xbf, 0x2d, 0x02, value, 0x00])
        payload[3] = self.compute_checksum(3, payload)
        self._send_message(payload)

    def set_hold_mode(self, value):
        payload = bytearray([0x0a, 0xbf, 0x1d, 0x00, value, 0x00])
        payload[3] = self.compute_checksum(3, payload)
        self._send_message(payload)

    def set_filter2_enabled(self, value):
        self.filter_2_enabled = value

    async def set_current_time(self):
        from homeassistant.util.dt import now
        current_time = now()
        hour = current_time.hour
        minute = current_time.minute
        payload = bytearray([0x0a, 0xbf, 0x11, 0x00, 0x04, hour, minute, 0x00])
        payload[3] = self.compute_checksum(3, payload)
        self._send_message(payload)

    def set_filter_cycle_begins_time(self, filter_num, time_value):
        if filter_num == 1:
            self.filter_1_begins_hour = time_value.hour
            self.filter_1_begins_minute = time_value.minute
        elif filter_num == 2:
            self.filter_2_begins_hour = time_value.hour
            self.filter_2_begins_minute = time_value.minute

    def set_filter_cycle_runs_time(self, filter_num, time_value):
        if filter_num == 1:
            self.filter_1_runs_hour = time_value.hour
            self.filter_1_runs_minute = time_value.minute
        elif filter_num == 2:
            self.filter_2_runs_hour = time_value.hour
            self.filter_2_runs_minute = time_value.minute