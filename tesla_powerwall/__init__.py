from typing import Union

import requests
from urllib.parse import urljoin, urlparse, urlunparse, urlsplit, urlunsplit
from requests import Session
from requests.packages.urllib3.exceptions import InsecureRequestWarning

from .const import (
    User,
    GridStatus,
    GridState,
    LineStatus,
    OperationMode,
    SUPPORTED_OPERATION_MODES,
    MeterType,
    DeviceType,
)
from .error import (
    ApiError,
    PowerwallUnreachableError,
    AccessDeniedError
)
from .responses import (
    MetersAggregateResponse,
    MetersResponse, 
    SiteinfoResponse, 
    SitemasterResponse, 
    CustomerRegistrationResponse,
    PowerwallStatusResponse,
    PowerwallsStatusResponse
)

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

VERSION = "0.1.4"


class Powerwall(object):
    def __init__(self, endpoint : str, timeout : int=10, http_session : requests.Session=None, verify_ssl : bool=False):
        if endpoint.startswith("https"):
            self._endpoint = endpoint
        elif endpoint.startswith("http"):
            self._endpoint = endpoint.replace("http", "https")
        else:
            self._endpoint = f"https://{endpoint}"

        if not self._endpoint.endswith("api") and not self._endpoint.endswith("/"):
            self._endpoint += "/api/"
        elif self._endpoint.endswith("api"):
            self._endpoint += "/"
        elif self._endpoint.endswith("/") and not self._endpoint.endswith("api/"):
            self._endpoint += "api/"

        self._timeout = timeout
        self._http_session = http_session if http_session else Session()
        self._http_session.verify = verify_ssl

    def _process_response(self, response : str) -> dict:
        if response.status_code == 404:
            raise ApiError(f"The url {response.request.path_url} returned error 404")

        if response.status_code == 401 or response.status_code == 403:
            response_json = None
            try:
                response_json = response.json()
            except Exception:
                raise AccessDeniedError(response.request.path_url)
            else:
                raise AccessDeniedError(
                    response.request.path_url, response_json["error"])

        if response.status_code == 502:
            raise PowerwallUnreachableError()

        response_json = response.json()

        if response_json is None:
            return {}

        if "error" in response_json:
            raise ApiError(response_json["error"])

        return response_json

    def _get(self, path: str, needs_authentication : bool=False, headers: dict = {}):
        if needs_authentication is True and not "Authorization" in self._http_session.headers.keys():
            raise ApiError(f"Authentication required to access {path}")
        
        try:
            response = self._http_session.get(
                url=urljoin(self._endpoint, path),
                timeout=self._timeout,
                headers=headers,
            )
        except requests.exceptions.ConnectionError:
            raise PowerwallUnreachableError

        return self._process_response(response)

    def _post(self, path: str, payload: dict, needs_authentication : bool=False, headers: dict = {}):
        if needs_authentication and not "Authorization" in self._http_session.headers.keys():
            raise ApiError(f"Authentication required to access {path}")

        try:
            response = self._http_session.post(
                url=urljoin(self._endpoint, path),
                data=payload,
                timeout=self._timeout,
                headers=headers,
            )
        except requests.exceptions.ConnectionError:
            raise PowerwallUnreachableError

        return self._process_response(response)

    def login(self, user : Union[User, str], email : str, password : str):
        if isinstance(user, User):
            user = user.value
            
        response = self._post(
            "login/Basic",
            {"username": user, "email": email,
                "password": password, "force_sm_off": True},
        )

        token = response["token"]

        self._http_session.headers["Authorization"] = "Bearer " + token

    def run(self):
        self._get("sitemaster/run", True)

    def stop(self):
        self._get("sitemaster/stop", True)

    def set_run_for_commissioning(self):
        self._post("sitemaster/run_for_commissioning", True)

    def get_charge(self) -> float:
        """Returns current charge of powerwall"""
        return self._get("system_status/soe")["percentage"]

    def get_sitemaster(self) -> SitemasterResponse:
        return SitemasterResponse(self._get("sitemaster"))

    def get_meters(self) -> MetersAggregateResponse:
        """Returns the different meters in a MetersAggregateResponse"""
        return MetersAggregateResponse(self._get("meters/aggregates"))

    def get_meter_detailed(self, meter : MeterType) -> Union[list, dict]:
        """Returns details about a specific meter
        
        If their are no details available for a meter an empty dict is returned.
        """
        return self._get(f"meters/{meter.value}")

    def grid_status(self) -> GridStatus:
        """Returns the current grid status."""
        return GridStatus(self._get("system_status/grid_status")["grid_status"])

    @property
    def grid_services_active(self):
        return self._get("system_status/grid_status")["grid_services_active"]

    @property
    def grid_codes(self):
        return self._get("site_info/grid_codes")

    @property
    def site_info(self) -> SiteinfoResponse:
        """
        Returns information about the powerwall site

        """
        return SiteinfoResponse(self._get("site_info"))

    def set_site_name(self, site_name: str):
        return self._post("site_info/site_name", {"site_name": site_name}, True)

    def get_status(self) -> PowerwallStatusResponse:
        return PowerwallStatusResponse(self._get("status"))

    def get_powerwalls_status(self) -> PowerwallsStatusResponse:
        return PowerwallsStatusResponse(self._get('powerwalls/status'))

    @property
    def device_type(self) -> DeviceType:
        """Returns the device type of the powerwall"""
        return DeviceType(self._get("device_type")["device_type"])

    @property
    def customer_registration(self):
        return CustomerRegistrationResponse(self._get("customer/registration"))

    @property
    def load_power(self):
        return self.meters.load.instant_power

    @property
    def site_power(self):
        return self.site.meters.instant_power

    @property
    def solar_power(self):
        return self.meters.solar.instant_power

    @property
    def battery_power(self):
        return self.meters.battery.instant_power

    @property
    def operation(self):
        return self._get("operation", True)

    @property
    def mode(self):
        return self.operation["real_mode"]

    @property
    def backup_preserve_percentage(self):
        return self.operation["backup_reserve_percentage"]

    def set_mode_and_backup_preserve_percentage(self, mode, percentage):
        self._post("operation", {"mode": mode, "percentage": percentage})

    def set_backup_preserve_percentage(self, percentage):
        self.set_mode_and_backup_preserve_percentage(self.mode, percentage)

    def set_mode(self, mode):
        self.set_mode_and_backup_preserve_percentage(
            mode, self.backup_preserve_percentage)

    def get_phase_usage(self):
        resp = self._get('powerwalls/phase_usages', needs_authentication=True)
        return resp



    def is_solar_active(self):
        return not self.meters.site

    def is_sending_to_grid(self):
        return self.meters.site.instant_total_current > 0

    def is_drawing_from_grid(self):
        return not self.is_sending_to_grid()

    def is_sending_to_battery(self):
        return self.meters.battery.instant_total_current > 0

    def is_drawing_from_battery(self):
        return not self.is_sending_to_battery()

    def is_sending_to_solar(self):
        return self.meters.solar.instant_total_current > 0

    def is_drawing_from_solar(self):
        return not self.is_sending_to_solar()

    def is_sending_to_load(self):
        return self.meters.load.instant_total_current > 0

    def power_send_to_load(self, meters=None):
        pass

    def power_send_to_grid(self, meters=None):
        pass

    def power_send_to_battery(self, meters=None):
        pass

    def __del__(self):
        if self._http_session is not None:
            self._http_session.close()
