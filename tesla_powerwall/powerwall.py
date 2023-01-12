from typing import List, Union

import requests

from .api import API
from .const import (
    DEFAULT_KW_ROUND_PERSICION,
    SUPPORTED_OPERATION_MODES,
    DeviceType,
    GridState,
    GridStatus,
    IslandMode,
    LineStatus,
    MeterType,
    OperationMode,
    Roles,
    SyncType,
    User,
)
from .helpers import assert_attribute
from .responses import (
    Battery,
    LoginResponse,
    Meter,
    MetersAggregates,
    PowerwallStatus,
    SiteInfo,
    SiteMaster,
    Solar,
)


class Powerwall:
    def __init__(
        self,
        endpoint: str,
        timeout: int = 10,
        http_session: Union[requests.Session, None] = None,
        verify_ssl: bool = False,
        disable_insecure_warning: bool = True,
    ):
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
        return self.login_as(User.CUSTOMER, password, email, force_sm_off)

    def logout(self) -> None:
        self._api.logout()

    def is_authenticated(self) -> bool:
        return self._api.is_authenticated()

    def run(self) -> None:
        self._api.get_sitemaster_run()

    def stop(self) -> None:
        self._api.get_sitemaster_stop()

    def get_charge(self) -> Union[float, int]:
        return assert_attribute(self._api.get_system_status_soe(), "percentage", "soe")

    def get_energy(self) -> int:
        return assert_attribute(
            self._api.get_system_status(), "nominal_energy_remaining", "system_status"
        )

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

    def get_capacity(self) -> float:
        return assert_attribute(
            self._api.get_system_status(), "nominal_full_pack_energy", "system_status"
        )

    def get_batteries(self) -> List[Battery]:
        batteries = assert_attribute(
            self._api.get_system_status(), "battery_blocks", "system_status"
        )
        return [Battery(battery) for battery in batteries]

    def is_grid_services_active(self) -> bool:
        return assert_attribute(
            self._api.get_system_status_grid_status(),
            "grid_services_active",
            "grid_status",
        )

    def get_site_info(self) -> SiteInfo:
        """Returns information about the powerwall site"""
        return SiteInfo(self._api.get_site_info())

    def set_site_name(self, site_name: str) -> str:
        return self._api.post_site_info_site_name({"site_name": site_name})

    def get_status(self) -> PowerwallStatus:
        return PowerwallStatus(self._api.get_status())

    def get_device_type(self) -> DeviceType:
        """Returns the device type of the powerwall"""
        return self.get_status().device_type

    def get_serial_numbers(self) -> List[str]:
        powerwalls = assert_attribute(
            self._api.get_powerwalls(), "powerwalls", "powerwalls"
        )
        return [
            assert_attribute(powerwall, "PackageSerialNumber")
            for powerwall in powerwalls
        ]

    def get_gateway_din(self) -> str:
        """Return the gateway din."""
        return assert_attribute(self._api.get_powerwalls(), "gateway_din", "powerwalls")

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

    def set_island_mode(self, mode: IslandMode) -> IslandMode:
        return IslandMode(assert_attribute(self._api.post_islanding_mode({"island_mode": mode.value}), "island_mode"))

    def get_version(self) -> str:
        version_str = assert_attribute(self._api.get_status(), "version", "status")
        return version_str.split(" ")[
            0
        ]  # newer versions include a sha trailer '21.44.1 c58c2df3'

    def get_api(self) -> API:
        return self._api

    def close(self) -> None:
        self._api.close()
