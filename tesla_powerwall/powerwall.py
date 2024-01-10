from types import TracebackType
from typing import List, Union, Optional, Type

import aiohttp

from .api import API
from .const import DeviceType, GridStatus, IslandMode, OperationMode, User
from .error import ApiError
from .helpers import assert_attribute
from .responses import (
    BatteryResponse,
    LoginResponse,
    MeterDetailsResponse,
    MetersAggregatesResponse,
    PowerwallStatusResponse,
    SiteInfoResponse,
    SiteMasterResponse,
    SolarResponse,
)


class Powerwall:
    def __init__(
        self,
        endpoint: str,
        timeout: int = 10,
        http_session: Union[aiohttp.ClientSession, None] = None,
        verify_ssl: bool = False,
        disable_insecure_warning: bool = True,
    ):
        self._api = API(
            endpoint=endpoint,
            timeout=timeout,
            http_session=http_session,
            verify_ssl=verify_ssl,
            disable_insecure_warning=disable_insecure_warning,
        )

    async def login_as(
        self,
        user: Union[User, str],
        password: str,
        email: str,
        force_sm_off: bool = False,
    ) -> LoginResponse:
        if isinstance(user, User):
            user = user.value

        response = await self._api.login(user, email, password, force_sm_off)
        # The api returns an auth cookie which is automatically set
        # so there is no need to further process the response

        return LoginResponse.from_dict(response)

    async def login(
        self, password: str, email: str = "", force_sm_off: bool = False
    ) -> LoginResponse:
        return await self.login_as(User.CUSTOMER, password, email, force_sm_off)

    async def logout(self) -> None:
        await self._api.logout()

    def is_authenticated(self) -> bool:
        return self._api.is_authenticated()

    async def run(self) -> None:
        await self._api.get_sitemaster_run()

    async def stop(self) -> None:
        await self._api.get_sitemaster_stop()

    async def get_charge(self) -> Union[float, int]:
        return assert_attribute(
            await self._api.get_system_status_soe(), "percentage", "soe"
        )

    async def get_energy(self) -> int:
        return assert_attribute(
            await self._api.get_system_status(),
            "nominal_energy_remaining",
            "system_status",
        )

    async def get_sitemaster(self) -> SiteMasterResponse:
        return SiteMasterResponse.from_dict(await self._api.get_sitemaster())

    async def get_meters(self) -> MetersAggregatesResponse:
        return MetersAggregatesResponse.from_dict(
            await self._api.get_meters_aggregates()
        )

    async def get_meter_site(self) -> MeterDetailsResponse:
        meter_response = await self._api.get_meters_site()
        if meter_response is None or len(meter_response) == 0:
            raise ApiError("The powerwall returned no values for the site meter")

        return MeterDetailsResponse.from_dict(meter_response[0])

    async def get_meter_solar(self) -> MeterDetailsResponse:
        meter_response = await self._api.get_meters_solar()
        if meter_response is None or len(meter_response) == 0:
            raise ApiError("The powerwall returned no values for the solar meter")

        return MeterDetailsResponse.from_dict(meter_response[0])

    async def get_grid_status(self) -> GridStatus:
        """Returns the current grid status."""
        status = assert_attribute(
            await self._api.get_system_status_grid_status(),
            "grid_status",
            "grid_status",
        )

        return GridStatus(status)

    async def get_capacity(self) -> float:
        return assert_attribute(
            await self._api.get_system_status(),
            "nominal_full_pack_energy",
            "system_status",
        )

    async def get_batteries(self) -> List[BatteryResponse]:
        batteries = assert_attribute(
            await self._api.get_system_status(), "battery_blocks", "system_status"
        )
        return [BatteryResponse.from_dict(battery) for battery in batteries]

    async def is_grid_services_active(self) -> bool:
        return assert_attribute(
            await self._api.get_system_status_grid_status(),
            "grid_services_active",
            "grid_status",
        )

    async def get_site_info(self) -> SiteInfoResponse:
        """Returns information about the powerwall site"""
        return SiteInfoResponse.from_dict(await self._api.get_site_info())

    async def set_site_name(self, site_name: str) -> dict:
        return await self._api.post_site_info_site_name({"site_name": site_name})

    async def get_status(self) -> PowerwallStatusResponse:
        return PowerwallStatusResponse.from_dict(await self._api.get_status())

    async def get_device_type(self) -> DeviceType:
        """Returns the device type of the powerwall"""
        return (await self.get_status()).device_type

    async def get_serial_numbers(self) -> List[str]:
        powerwalls = assert_attribute(
            await self._api.get_powerwalls(), "powerwalls", "powerwalls"
        )
        return [
            assert_attribute(powerwall, "PackageSerialNumber")
            for powerwall in powerwalls
        ]

    async def get_gateway_din(self) -> str:
        """Return the gateway din."""
        return assert_attribute(
            await self._api.get_powerwalls(), "gateway_din", "powerwalls"
        )

    async def get_operation_mode(self) -> OperationMode:
        operation_mode = assert_attribute(
            await self._api.get_operation(), "real_mode", "operation"
        )
        return OperationMode(operation_mode)

    async def get_backup_reserve_percentage(self) -> float:
        return assert_attribute(
            await self._api.get_operation(), "backup_reserve_percent", "operation"
        )

    async def get_solars(self) -> List[SolarResponse]:
        return [
            SolarResponse.from_dict(solar) for solar in await self._api.get_solars()
        ]

    async def get_vin(self) -> str:
        return assert_attribute(await self._api.get_config(), "vin", "config")

    async def set_island_mode(self, mode: IslandMode) -> IslandMode:
        return IslandMode(
            assert_attribute(
                await self._api.post_islanding_mode({"island_mode": mode.value}),
                "island_mode",
            )
        )

    async def get_version(self) -> str:
        version_str = assert_attribute(
            await self._api.get_status(), "version", "status"
        )
        return version_str.split(" ")[
            0
        ]  # newer versions include a sha trailer '21.44.1 c58c2df3'

    def get_api(self) -> API:
        return self._api

    async def close(self) -> None:
        await self._api.close()

    async def __aenter__(self) -> "Powerwall":
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        await self.close()
