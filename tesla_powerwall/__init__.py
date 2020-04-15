from json.decoder import JSONDecodeError
from typing import List, Union
from urllib.parse import urljoin, urlparse, urlsplit, urlunparse, urlunsplit

import requests
from requests import Session
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning

from .const import (
    DEFAULT_KW_ROUND_PERSICION,
    SUPPORTED_OPERATION_MODES,
    SUPPORTED_POWERWALL_VERSIONS,
    DeviceType,
    GridState,
    GridStatus,
    LineStatus,
    MeterType,
    OperationMode,
    User,
)
from .error import AccessDeniedError, ApiError, PowerwallUnreachableError
from .helpers import convert_to_kw
from .responses import (
    CustomerRegistrationResponse,
    ListPowerwallsResponse,
    LoginResponse,
    MeterDetailsResponse,
    MetersAggregateResponse,
    MetersResponse,
    PowerwallsStatusResponse,
    PowerwallStatusResponse,
    SiteInfoResponse,
    SitemasterResponse,
    SolarsResponse,
)

VERSION = "0.2.4"


class Powerwall(object):
    def __init__(
        self,
        endpoint: str,
        timeout: int = 10,
        http_session: requests.Session = None,
        verify_ssl: bool = False,
        disable_insecure_warning: bool = True,
    ):

        if disable_insecure_warning:
            disable_warnings(InsecureRequestWarning)

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

        self._token = None

    def _process_response(self, response: str) -> dict:
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
                    response.request.path_url, response_json["error"]
                )

        if response.status_code == 502:
            raise PowerwallUnreachableError()

        try:
            response_json = response.json()
        except JSONDecodeError:
            raise ApiError(f"Error while decoding json of response: {response.text}")

        if response_json is None:
            return {}

        if "error" in response_json:
            raise ApiError(response_json["error"])

        return response_json

    def _get(
        self, path: str, needs_authentication: bool = False, headers: dict = {}
    ) -> dict:
        if needs_authentication and not self.is_authenticated():
            raise ApiError(f"Authentication required to access {path}")

        try:
            response = self._http_session.get(
                url=urljoin(self._endpoint, path),
                timeout=self._timeout,
                headers=headers,
            )
        except requests.exceptions.ConnectionError as e:
            raise PowerwallUnreachableError(e)

        return self._process_response(response)

    def _post(
        self,
        path: str,
        payload: dict,
        needs_authentication: bool = False,
        headers: dict = {},
    ) -> dict:
        if needs_authentication and not self.is_authenticated():
            raise ApiError(f"Authentication required to access {path}")

        try:
            response = self._http_session.post(
                url=urljoin(self._endpoint, path),
                data=payload,
                timeout=self._timeout,
                headers=headers,
            )
        except requests.exceptions.ConnectionError as e:
            raise PowerwallUnreachableError(e)

        return self._process_response(response)

    def is_authenticated(self) -> bool:
        return "AuthCookie" in self._http_session.cookies.keys()

    def login_as(
        self,
        user: Union[User, str],
        email: str,
        password: str,
        force_sm_off: bool = False,
    ) -> LoginResponse:
        if isinstance(user, User):
            user = user.value

        # force_sm_off is referred to as 'shouldForceLogin' in the web source code
        response = self._post(
            "login/Basic",
            {
                "username": user,
                "email": email,
                "password": password,
                "force_sm_off": force_sm_off,
            },
        )

        # The api returns an auth cookie which is automatically set
        # so there is no need to further process the response

        return LoginResponse(response)

    def login(
        self, email: str, password: str, force_sm_off: bool = False
    ) -> LoginResponse:
        return self.login_as(User.CUSTOMER, email, password, force_sm_off)

    def logout(self):
        if not self.is_authenticated():
            raise ApiError("Must be logged in to log out")
        # The api unsets the auth cookie and the token is invalidated
        self._get("logout", True)

    def run(self):
        self._get("sitemaster/run", True)

    def stop(self):
        self._get("sitemaster/stop", True)

    def get_charge(self, rounded: bool = True) -> Union[float, int]:
        """Returns current charge of powerwall"""
        charge = self._get("system_status/soe")["percentage"]
        if rounded:
            return round(charge)
        else:
            return charge

    def get_sitemaster(self) -> SitemasterResponse:
        return SitemasterResponse(self._get("sitemaster"))

    def get_meters(self) -> MetersAggregateResponse:
        """Returns the different meters in a MetersAggregateResponse"""
        return MetersAggregateResponse(self._get("meters/aggregates"))

    def get_meter_details(
        self, meter: MeterType
    ) -> Union[List[MeterDetailsResponse], None]:
        """Returns details about a specific meter. 
        If their are no details available for a meter None is returned."""
        resp = self._get(f"meters/{meter.value}")
        if isinstance(resp, list):
            return [MeterDetailsResponse(item) for item in resp]
        elif isinstance(resp, dict):
            return None

    def get_meter_readings(self) -> dict:
        return self._get("meter/readings", True)

    def get_grid_status(self) -> GridStatus:
        """Returns the current grid status."""
        return GridStatus(self._get("system_status/grid_status")["grid_status"])

    def get_grid_services_active(self) -> bool:
        return self._get("system_status/grid_status")["grid_services_active"]

    def get_grid_codes(self) -> list:
        """Returns all available grid codes"""
        return self._get("site_info/grid_codes", needs_authentication=True)

    def get_site_info(self) -> SiteInfoResponse:
        """Returns information about the powerwall site"""
        return SiteInfoResponse(self._get("site_info"))

    def set_site_name(self, site_name: str):
        return self._post("site_info/site_name", {"site_name": site_name}, True)

    def get_status(self) -> PowerwallStatusResponse:
        return PowerwallStatusResponse(self._get("status"))

    def get_powerwalls_status(self) -> PowerwallsStatusResponse:
        return PowerwallsStatusResponse(self._get("powerwalls/status", True))

    def get_device_type(self) -> DeviceType:
        """Returns the device type of the powerwall"""
        return DeviceType(self._get("device_type")["device_type"])

    def get_customer_registration(self) -> CustomerRegistrationResponse:
        return CustomerRegistrationResponse(self._get("customer/registration"))

    def get_powerwalls(self) -> ListPowerwallsResponse:
        """Returns powerwalls and status"""
        return ListPowerwallsResponse(self._get("powerwalls"))

    def get_operation_mode(self) -> OperationMode:
        return OperationMode(self._get("operation", True)["real_mode"])

    def get_backup_preserve_percentage(self) -> float:
        return self._get("operation", True)["backup_reserve_percentage"]

    # def set_mode_and_backup_preserve_percentage(self, mode, percentage):
    #     self._post("operation", {"mode": mode, "percentage": percentage})

    # def set_backup_preserve_percentage(self, percentage):
    #     self.set_mode_and_backup_preserve_percentage(self.mode, percentage)

    # def set_mode(self, mode):
    #     self.set_mode_and_backup_preserve_percentage(
    #         mode, self.backup_preserve_percentage)

    def get_networks(self) -> list:
        return self._get("networks")

    def get_phase_usage(self):
        return self._get("powerwalls/phase_usages", needs_authentication=True)

    def set_run_for_commissioning(self):
        self._post("sitemaster/run_for_commissioning", True)

    def get_solars(self) -> List[SolarsResponse]:
        solars = self._get("solars", needs_authentication=True)
        return [SolarsResponse(solar) for solar in solars]

    def get_vin(self) -> str:
        return self._get("config", needs_authentication=True)["vin"]

    def get_logs(self) -> str:
        return self._get("getlogs", needs_authentication=True)

    def get_meters_info(self) -> list:
        return self._get("meters", needs_authentication=True)

    def get_installer_info(self) -> dict:
        return self._get("installer", needs_authentication=True)

    def get_solar_brands(self) -> List[str]:
        return self._get("solars/brands", needs_authentication=True)

    def get_version(self) -> str:
        return self.get_status().version

    def get_git_hash(self) -> str:
        return self.get_status().git_hash

    def is_sending_to(self, meter: MeterType, rounded=True) -> bool:
        """Wrapper method for is_sending_to"""
        return self.get_meters().get(meter).is_sending_to()

    def is_drawing_from(self, meter: MeterType) -> bool:
        """Wrapper method for is_drawing_from"""
        return self.get_meters().get(meter).is_drawing_from()

    def is_active(self, meter: MeterType) -> bool:
        """Wrapper method for is_active()"""
        return self.get_meters().get(meter).is_active()

    def get_power(self, meter: MeterType) -> bool:
        return self.get_meters().get(meter).get_power()

    def is_powerwall_version_supported(self) -> bool:
        return self.get_version() in SUPPORTED_POWERWALL_VERSIONS
