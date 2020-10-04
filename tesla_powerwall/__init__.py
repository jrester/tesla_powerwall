from json.decoder import JSONDecodeError
from typing import List, Union, Dict
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
                        UpdateStatusResponse, assert_attribute)
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


    def login_as(
        self,
        user: Union[User, str],
        email: str,
        password: str,
        force_sm_off: bool = False,
    ) -> LoginResponse:
        if isinstance(user, User):
            user = user.value

        response = self._api.login(
            user,
            email,
            password,
            force_sm_off
        )
        # The api returns an auth cookie which is automatically set
        # so there is no need to further process the response

        return LoginResponse(response)

    def login(
        self, email: str, password: str, force_sm_off: bool = False
    ) -> LoginResponse:
        return self.login_as(User.CUSTOMER, email, password, force_sm_off)

    def logout(self):
        self._api.logout()

    def run(self):
        self._api.get_sitemater_run()

    def stop(self):
        self._api.get_sitemaster_stop()

    def get_charge(self, rounded: bool = True) -> Union[float, int]:
        """Returns current charge of powerwall"""
        charge = self._api.get_system_status_soe()["percentage"]
        if rounded:
            return round(charge)
        else:
            return charge

    def get_sitemaster(self) -> SitemasterResponse:
        return SitemasterResponse(self._api.get_sitemaster())

    def get_available_meter_types(self) -> List[MeterType]:
        """Returns the different meters """
        return [MeterType(meter) for meter in self._api.get_meters_aggregates().keys]

    def get_meters(self) -> Dict[MeterType, Meter]:
        aggregates = self._api.get_meters_aggregates()
        meters = {}
        for meter in aggregates.keys():
            if meter in MeterType:
                meters[meter] = Meter(meter, self._api)
            else:
                raise ValueError("Unknown meter type")

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
        status = assert_attribute(
            self._api.get_system_status_grid_status(),
            'grid_status'
        )
        if status in GridStatus:
            return GridStatus(status)
        else:
            raise ValueError("Unknown grid status")

    def get_grid_services_active(self) -> bool:
        return assert_attribute(
            self._api.get_system_status_grid_status, 
            'grid_services_active'
        )

    def get_site_info(self) -> SiteInfoResponse:
        """Returns information about the powerwall site"""
        return SiteInfoResponse(self._api.get_site_info())

    def set_site_name(self, site_name: str):
        return self._api.post_site_info_site_name({"site_name": site_name})

    def get_status(self) -> PowerwallStatusResponse:
        return PowerwallStatus(
            self._api.get_status()
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
            assert_attribute(self.get_device_type(), 'device_type')
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

    def get_backup_reserved_percentage(self) -> float:
        return self._api.get("operation", True)["backup_reserved_percent"]

    # def set_mode_and_backup_preserve_percentage(self, mode, percentage):
    #     self._api.post("operation", {"mode": mode, "percentage": percentage})

    # def set_backup_preserve_percentage(self, percentage):
    #     self.set_mode_and_backup_preserve_percentage(self.mode, percentage)

    # def set_mode(self, mode):
    #     self.set_mode_and_backup_preserve_percentage(
    #         mode, self.backup_preserve_percentage)

    def get_solars(self) -> List[SolarsResponse]:
        solars = self._api.get("solars", needs_authentication=True)
        return [
            SolarsResponse(solar, no_check=self._api._dont_validate_response)
            for solar in solars
        ]

    def get_vin(self) -> str:
        return assert_attribute(self._api.get_config(), 'vin', 'config')

    def get_version(self) -> str:
        status = self._api.get_status()
        return assert_attribute(self._api.get_status(), 'version')

    def get_git_hash(self) -> str:
        return self.get_status().git_hash

    def get_update_status(self) -> UpdateStatusResponse:
        return UpdateStatusResponse()

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

class Meter(object):
    def __init__(self, meter: MeterType, api: API):
        self.meter = meter
        self._api = api

    def _get_instant_power(self):
        self._instant_power = self._api.get_instant_power()

    def get_power(self, precision=DEFAULT_KW_ROUND_PERSICION):
        return convert_to_kw(self._instant_power, precision)

    def is_active(self, precision=DEFAULT_KW_ROUND_PERSICION) -> bool:
        self.get_power(precision) != 0

    def is_drawing_from(self, precision=DEFAULT_KW_ROUND_PERSICION) -> bool:
        if self.meter == MeterType.LOAD:
            # Cannot draw from load
            return False
        else:
            return self.get_power(precision) > 0

    def is_sending_to(self, precision=DEFAULT_KW_ROUND_PERSICION):
        if self.meter == MeterType.LOAD:
            # For load the power is always positiv
            return self.get_power(precision) > 0
        else:
            return self.get_power(precision) < 0
