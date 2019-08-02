import requests
import logging
import sys

from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

logging.basicConfig(stream=sys.stdout)

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)

GRID_STATUS_SYSTEM_GRID_UP = "SystemGridConnected"
GRID_STATUS_SYSTEM_GRID_DOWN = "SystemIslandedActive"
GRID_STATUS_SYSTEM_GRID_RESTORED_NO_SYNC = "SystemTransitionToGrid"

OPERATION_MODE_SELF_CONSUMPTION = "self_consumption"
OPERATION_MODE_BACKUP = "backup"
OPERATION_MODE_TIME_OF_USE = "autonomus"
OPERATION_MODE_SCHEDULER = "scheduler"

BACKUP_RESERVE_PERCENTAGE_5 = 10
BACKUP_RESERVE_PERCENTAGE_16 = 20
BACKUP_RESERVE_PERCENTAGE_20 = 24
BACKUP_RESERVE_PERCENTAGE_21 = 24.6
BACKUP_RESERVE_PERCENTAGE_30 = 33
BACKUP_RESERVE_PERCENTAGE_100 = 100

class ApiError(Exception):
    def __init__(self, error):
        super().__init__(f"Power Wall api error: {error}")

class PowerWallUnreachableError(Exception):
    def __init__(self):
        super().__init__(f"Site master or Power wall is unreachable!")

class InvalidPassword(Exception):
    def __init__(self,):
        super().__init__(f'Invalid password')

class MetersResponse:
    JSON_ATTRS = ["last_communication_time", "instant_power", "instant_reactive_power", "instant_apparent_power", "frequency", "energy_exported", "energy_imported", "instant_average_voltage", "instant_total_current", "i_a_current", "i_b_current", "i_c_current"]

    def __init__(self, response_json):
        self.response_json = response_json

        for attr in MetersResponse.JSON_ATTRS:
            setattr(self, attr, response_json[attr])

class PowerWall:
    def __init__(self, host, password=None):
        self.host = host
        self.password = password
        self.token = None
        self.auth_header = {}
        self._login_flag = False

    def _process_response(self, response):
        if response.status_code == 401:
            if self._login_flag:
                raise InvalidPassword()

            self.login()

        if response.status_code == 502:
            raise PowerWallUnreachableError()

        _LOGGER.debug(f"Response: {response.text}")
        response_json = response.json()

        if 'error' in response_json:
            raise ApiError(response_json['error'])

        return response_json

    def _get(self, endpoint, needs_authentication=False):
        _LOGGER.debug(f'Getting https://{self.host}/{endpoint}')

        header = {}
        if needs_authentication and self.token is None:
            _LOGGER.debug("Authenticating")
            self.login()

        response = requests.get(url=f'https://{self.host}/{endpoint}', verify=False, headers=self.auth_header)

        return self._process_response(response)
        
    def _post(self, endpoint : str, payload : dict, needs_authentication=False):
        _LOGGER.debug(f"Post {payload} to https://{self.host}/{endpoint}")

        if needs_authentication and self.token is None:
            _LOGGER.debug("Authenticating")
            self.login()

        response = requests.post(url=f'https://{self.host}/{endpoint}', data=payload, verify=False, headers=self.auth_header)

        return self._process_response(response)

    def login(self):
        self._login_flag = True

        if self.password is None:
            raise InvalidPassword()

        response = self._post('api/login/Basic', {'username': '', 'password': self.password, 'force_sm_off': True})
            
        self.token = response['token']
        _LOGGER.debug(f'Received new token {self.token}')
        self.auth_header = {'Authorization': 'Bearer ' + self.token}
        self.run()

        self._login_flag = False

    def run(self):
        self._get("api/sitemaster/run")
        
    @property
    def charge(self):
        return self._get('api/system_status/soe')['percentage']

    @property
    def sitemaster(self):
        return self._get("api/sitemaster")

    @property
    def running(self):
        return self.sitemaster["running"]

    @property
    def uptime(self):
        return self.sitemaster["uptime"]

    @property
    def connected_to_tesla(self):
        return self.sitemaster["connected_to_tesla"]

    @property
    def meters(self):
        return self._get("api/meters/aggregates")
    
    @property
    def solar(self):
        return MetersResponse(self.meters["solar"])

    @property
    def grid(self):
        return MetersResponse(self.meters["site"])

    @property
    def load(self):
        return MetersResponse(self.meters["load"])

    @property
    def battery(self):
        return MetersResponse(self.meters["battery"])

    @property
    def busway(self):
        return MetersResponse(self.meters["busway"])

    @property
    def frequency(self):
        return MetersResponse(self.meters["frequency"])

    @property
    def generator(self):
        return MetersResponse(self.meters["generator"])

    @property
    def solar_detailed(self):
        return self._get("api/meters/solar")

    @property
    def grid_status(self):
        return self._get("api/system_status/grid_status")["grid_status"]

    @property
    def site_info(self):
        return self._get("api/site_info")

    @property
    def status(self):
        return self._get("api/site_info/status")

    @property
    def home_power(self):
        return self.load.instant_power

    @property
    def grid_power(self):
        return self.grid.instant_power

    @property
    def solar_power(self):
        return self.solar.instant_power
    
    @property
    def battery_power(self):
        return self.battery.instant_power

    @property
    def operation(self):
        return self._get("api/operation", True)

    @property
    def mode(self):
        return self.operation["mode"]
    
    @property
    def backup_preserve_percentage(self):
        return self.operation["backup_reserve_percentage"]

    def set_mode_and_backup_preserve_percentage(self, mode, percentage):
        self._post("api/operation", {"mode": mode, "percentage": percentage})

    def set_backup_preserve_percentage(self, percentage):
        set_mode_and_backup_preserve_percentage(self.mode, percentage)

    def set_mode(self, mode):
        set_mode_and_backup_preserve_percentage(mode, self.backup_preserve_percentage)

    def is_sending_to_grid(self):
        return self.grid_power < 0

    def is_drawing_from_grid(self):
        return not self.sending_to_grid

    def is_sending_to_battery(self):
        return self.battery_power < 0
    
    def is_drawing_from_battery(self):
        return not self.sending_to_battery

    def is_sending_to_solar(self):
        return self.solar_power < 0

    def is_drawing_from_solar(self):
        return not self.sending_to_solar