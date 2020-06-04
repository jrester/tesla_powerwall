from json.decoder import JSONDecodeError
from typing import List, Union
from urllib.parse import urljoin, urlparse, urlsplit, urlunparse, urlunsplit
from packaging import version
from contextlib import contextmanager

import requests
from requests import Session
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning

from .const import (DEFAULT_KW_ROUND_PERSICION, SUPPORTED_OPERATION_MODES,
                    SUPPORTED_POWERWALL_VERSIONS, DeviceType, GridState,
                    GridStatus, LineStatus, MeterType, OperationMode, User,
                    Version)
from .error import AccessDeniedError, APIError, PowerwallUnreachableError, APIChangedError, PowerwallError
from .helpers import convert_to_kw
from .responses import (CustomerRegistrationResponse, ListPowerwallsResponse,
                        LoginResponse, MeterDetailsResponse,
                        MetersAggregateResponse, MetersResponse,
                        PowerwallsStatusResponse, PowerwallStatusResponse,
                        SiteInfoResponse, SitemasterResponse, SolarsResponse,
                        UpdateStatusResponse)
from .api import API


VERSION = "0.2.9"



class Powerwall(object):
    def __init__(
        self,
        endpoint: str,
        timeout: int = 10,
        http_session: requests.Session = None,
        verify_ssl: bool = False,
        disable_insecure_warning: bool = True,
        dont_validate_response: bool = True,
        pin_version: str = None,
    ):

        self._api = API(
            endpoint,
            timeout,
            http_session,
            verify_ssl,
            disable_insecure_warning,
            dont_validate_response
        )

        self.pin_version(pin_version)

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
        response = self._api._post(
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

        return LoginResponse(response, no_check=self._api._dont_validate_response)

    def login(
        self, email: str, password: str, force_sm_off: bool = False
    ) -> LoginResponse:
        return self.login_as(User.CUSTOMER, email, password, force_sm_off)

    def logout(self):
        if not self.is_authenticated():
            raise APIError("Must be logged in to log out")
        # The api unsets the auth cookie and the token is invalidated
        self._api.get("logout", True)

    def run(self):
        self._api.get("sitemaster/run", True)

    def stop(self):
        self._api.get("sitemaster/stop", True)

    def get_charge(self, rounded: bool = True) -> Union[float, int]:
        """Returns current charge of powerwall"""
        charge = self._api.get("system_status/soe")["percentage"]
        if rounded:
            return round(charge)
        else:
            return charge

    def get_sitemaster(self) -> SitemasterResponse:
        return SitemasterResponse(
            self._api.get("sitemaster"), no_check=self._api._dont_validate_response
        )

    def get_meters(self) -> MetersAggregateResponse:
        """Returns the different meters in a MetersAggregateResponse"""
        return MetersAggregateResponse(
            self._api.get("meters/aggregates"), no_check=self._api._dont_validate_response
        )

    def get_meter_details(
        self, meter: MeterType
    ) -> Union[List[MeterDetailsResponse], None]:
        """Returns details about a specific meter. 
        If their are no details available for a meter None is returned."""
        resp = self._api.get("meters/{}".format(meter.value))
        if isinstance(resp, list):
            return [
                MeterDetailsResponse(item, no_check=self._api._dont_validate_response)
                for item in resp
            ]
        elif isinstance(resp, dict):
            return None

    def get_meter_readings(self) -> dict:
        return self._api.get("meter/readings", True)

    def get_grid_status(self) -> GridStatus:
        """Returns the current grid status."""
        return GridStatus(self._api.get("system_status/grid_status")["grid_status"])

    def get_grid_services_active(self) -> bool:
        return self._api.get("system_status/grid_status")["grid_services_active"]

    def get_grid_codes(self) -> list:
        """Returns all available grid codes"""
        return self._api.get("site_info/grid_codes", needs_authentication=True)

    def get_site_info(self) -> SiteInfoResponse:
        """Returns information about the powerwall site"""
        return SiteInfoResponse(
            self._api.get("site_info"), no_check=self._api._dont_validate_response
        )

    def set_site_name(self, site_name: str):
        return self._api.post("site_info/site_name", {"site_name": site_name}, True)

    def get_status(self) -> PowerwallStatusResponse:
        return PowerwallStatusResponse(
            self._api.get("status"), no_check=self._api._dont_validate_response
        )

    def get_powerwalls_status(self) -> PowerwallsStatusResponse:
        return PowerwallsStatusResponse(
            self._api.get("powerwalls/status", True), no_check=self._api._dont_validate_response
        )

    def get_device_type(self) -> DeviceType:
        """Returns the device type of the powerwall"""
        if self._pin_version is None or self._pin_version >= Version.v1_46_0.value:
            return self.get_status().device_type
        else:
            return DeviceType(self._api.get("device_type")["device_type"])

    def get_customer_registration(self) -> CustomerRegistrationResponse:
        return CustomerRegistrationResponse(
            self._api.get("customer/registration"), no_check=self._api._dont_validate_response
        )

    def get_powerwalls(self) -> ListPowerwallsResponse:
        """Returns powerwalls and status"""
        return ListPowerwallsResponse(
            self._api.get("powerwalls"), no_check=self._api._dont_validate_response
        )

    def get_serial_numbers(self) -> List[str]:
        return [
            powerwall.PackageSerialNumber
            for powerwall in self.get_powerwalls().powerwalls
        ]

    def get_operation_mode(self) -> OperationMode:
        return OperationMode(self._api.get("operation", True)["real_mode"])

    def get_backup_preserve_percentage(self) -> float:
        return self._api.get("operation", True)["backup_reserve_percentage"]

    # def set_mode_and_backup_preserve_percentage(self, mode, percentage):
    #     self._api.post("operation", {"mode": mode, "percentage": percentage})

    # def set_backup_preserve_percentage(self, percentage):
    #     self.set_mode_and_backup_preserve_percentage(self.mode, percentage)

    # def set_mode(self, mode):
    #     self.set_mode_and_backup_preserve_percentage(
    #         mode, self.backup_preserve_percentage)

    def get_networks(self) -> list:
        return self._api.get("networks")

    def get_phase_usage(self):
        return self._api.get("powerwalls/phase_usages", needs_authentication=True)

    def set_run_for_commissioning(self):
        self._api.post("sitemaster/run_for_commissioning", True)

    def get_solars(self) -> List[SolarsResponse]:
        solars = self._api.get("solars", needs_authentication=True)
        return [
            SolarsResponse(solar, no_check=self._api._dont_validate_response)
            for solar in solars
        ]

    def get_vin(self) -> str:
        return self._api.get("config", needs_authentication=True)["vin"]

    def get_logs(self) -> str:
        return self._api.get("getlogs", needs_authentication=True)

    def get_meters_info(self) -> list:
        return self._api.get("meters", needs_authentication=True)

    def get_installer_info(self) -> dict:
        return self._api.get("installer", needs_authentication=True)

    def get_solar_brands(self) -> List[str]:
        return self._api.get("solars/brands", needs_authentication=True)

    def get_version(self) -> str:
        return self.get_status().version

    def get_git_hash(self) -> str:
        return self.get_status().git_hash

    def get_update_status(self) -> UpdateStatusResponse:
        return UpdateStatusResponse(self._api.get("system/update/status", needs_authentication=True))

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

    def set_dont_validate_response(self, value):
        self._api._dont_validate_response = value

    @contextmanager
    def no_verify(self):
        self.set_dont_validate_response(True)
        try:
            yield
        finally:
            self.set_dont_validate_response(False)


    def detect_and_pin_version(self) -> str:
        """Does an unferified request to get powerwall version and pins it"""
        with self.no_verify():
            status = self.get_status()
            if status.has_key("version"):
                version = status.get("version")
            else:
                raise APIError(
                    "Could not detect version because the status response does not return the version"
                )

        self.pin_version(version)

    def pin_version(self, vers: Union[str, version.Version, Version]):
        if vers is None:
            self._pin_version = None
        else:
            if isinstance(vers, str):
                self._pin_version = version.parse(vers)
            elif isinstance(vers, Version):
                self._pin_version = vers.value
            else:
                self._pin_version = vers

    def get_pinned_version(self) -> version.Version:
        return self._pin_version

# class Meter(object):
#     def __init__(self):
        

#     def get_power(self):

#     def is_active(self):

#     def is_drawing_from(self):

#     def is_sending_to(self):
