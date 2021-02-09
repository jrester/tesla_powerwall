from typing import Union, List
import requests
from packaging import version

from .api import API
from .const import (
    DEFAULT_KW_ROUND_PERSICION,
    SUPPORTED_OPERATION_MODES,
    DeviceType,
    GridState,
    GridStatus,
    LineStatus,
    MeterType,
    OperationMode,
    Roles,
    SyncType,
    User,
)
from .responses import (
    LoginResponse,
    Meter,
    MetersAggregates,
    PowerwallStatus,
    SiteMaster,
    SiteInfo,
    Solar,
)
from .helpers import assert_attribute


class Powerwall:
    def __init__(
        self,
        endpoint: str,
        timeout: int = 10,
        http_session: requests.Session = None,
        verify_ssl: bool = False,
        disable_insecure_warning: bool = True,
        pin_version: Union[str, version.Version] = None,
    ):
        if pin_version is not None:
            self.pin_version(pin_version)
        else:
            self._pin_version = None

        self._api = API(
            endpoint,
            timeout,
            http_session,
            verify_ssl,
            disable_insecure_warning,
        )

    def login_as(
        self,
        user: Union[User, str],
        password: str,
        email: str,
        force_sm_off: bool = False,
    ) -> dict:
        if isinstance(user, User):
            user = user.value

        response = self._api.login(user, email, password, force_sm_off)
        # The api returns an auth cookie which is automatically set
        # so there is no need to further process the response

        return LoginResponse(response)

    def login(self, password: str, email: str = "", force_sm_off: bool = False) -> dict:
        return self.login_as(User.CUSTOMER, email, password, force_sm_off)

    def logout(self):
        self._api.logout()

    def is_authenticated(self) -> bool:
        return self._api.is_authenticated()

    def run(self):
        self._api.get_sitemater_run()

    def stop(self):
        self._api.get_sitemaster_stop()

    def get_charge(self) -> float:
        return assert_attribute(self._api.get_system_status_soe(), "percentage", "soe")

    def get_sitemaster(self) -> SiteMaster:
        return SiteMaster(self._api.get_sitemaster())

    def get_meters(self) -> MetersAggregates:
        return MetersAggregates(self._api.get_meters_aggregates())

    def get_grid_status(self) -> GridStatus:
        """Returns the current grid status."""
        status = assert_attribute(
            self._api.get_system_status_grid_status(), "grid_status", "grid_status"
        )

        return GridStatus(status)

    def is_grid_services_active(self) -> bool:
        return assert_attribute(
            self._api.get_system_status_grid_status(),
            "grid_services_active",
            "grid_status",
        )

    def get_site_info(self) -> SiteInfo:
        """Returns information about the powerwall site"""
        return SiteInfo(self._api.get_site_info())

    def set_site_name(self, site_name: str):
        return self._api.post_site_info_site_name({"site_name": site_name})

    def get_status(self) -> PowerwallStatus:
        return PowerwallStatus(self._api.get_status())

    def get_device_type(self) -> DeviceType:
        """Returns the device type of the powerwall"""
        if self._pin_version is None or self._pin_version >= version.parse("1.46.0"):
            return self.get_status().device_type
        else:
            return DeviceType(
                assert_attribute(
                    self._api.get_device_type(), "device_type", "device_type"
                )
            )

    def get_serial_numbers(self) -> List[str]:
        powerwalls = assert_attribute(
            self._api.get_powerwalls(), "powerwalls", "powerwalls"
        )
        return [
            assert_attribute(powerwall, "PackageSerialNumber")
            for powerwall in powerwalls
        ]

    def get_operation_mode(self) -> OperationMode:
        operation_mode = assert_attribute(
            self._api.get_operation(), "real_mode", "operation"
        )
        return OperationMode(operation_mode)

    def get_backup_reserve_percentage(self) -> float:
        return assert_attribute(
            self._api.get_operation(), "backup_reserve_percent", "operation"
        )

    def get_solars(self) -> List[Solar]:
        return [Solar(solar) for solar in self._api.get_solars()]

    def get_vin(self) -> str:
        return assert_attribute(self._api.get_config(), "vin", "config")

    def get_version(self) -> str:
        return assert_attribute(self._api.get_status(), "version", "status")

    def detect_and_pin_version(self) -> str:
        self.pin_version(self.get_version())
        return self._pin_version

    def pin_version(self, vers: Union[str, version.Version]):
        if isinstance(vers, version.Version):
            self._pin_version = vers
        else:
            self._pin_version = version.parse(vers)

    def get_pinned_version(self) -> version.Version:
        return self._pin_version

    def get_api(self):
        return self._api
