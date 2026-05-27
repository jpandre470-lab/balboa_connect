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