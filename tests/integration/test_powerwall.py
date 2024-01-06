import aiohttp
import asyncio
import unittest

from tesla_powerwall import GridStatus, IslandMode, MeterType, Powerwall
from tesla_powerwall.responses import (
    MeterResponse,
    MetersAggregatesResponse,
    PowerwallStatusResponse,
    SiteInfoResponse,
    SiteMasterResponse,
)
from tests.integration import POWERWALL_IP, POWERWALL_PASSWORD


class TestPowerwall(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Allow unsafe cookies so that folks can use IP addresses in their configs
        # See: https://docs.aiohttp.org/en/v3.7.3/client_advanced.html#cookie-safety
        jar = aiohttp.CookieJar(unsafe=True)
        self.http_session = aiohttp.ClientSession(cookie_jar=jar)

        self.powerwall = Powerwall(POWERWALL_IP, http_session=self.http_session)
        await self.powerwall.login(POWERWALL_PASSWORD)
        assert self.powerwall.is_authenticated()

    async def asyncTearDown(self):
        await self.powerwall.close()
        await self.http_session.close()

    async def test_get_charge(self) -> None:
        charge = await self.powerwall.get_charge()
        if charge < 100:
            self.assertIsInstance(charge, float)
        else:
            self.assertEqual(charge, 100)

    async def test_get_meters(self) -> None:
        meters = await self.powerwall.get_meters()
        self.assertIsInstance(meters, MetersAggregatesResponse)

        self.assertIsInstance(meters.get_meter(MeterType.BATTERY), MeterResponse)

        for meter_type in meters.meters:
            meter = meters.get_meter(meter_type)
            assert meter is not None
            meter.energy_exported
            meter.energy_imported
            meter.instant_power
            meter.last_communication_time
            meter.frequency
            meter.instant_average_voltage
            meter.get_energy_exported()
            meter.get_energy_imported()
            self.assertIsInstance(meter.get_power(), float)
            self.assertIsInstance(meter.is_active(), bool)
            self.assertIsInstance(meter.is_drawing_from(), bool)
            self.assertIsInstance(meter.is_sending_to(), bool)

    async def test_sitemaster(self) -> None:
        sitemaster = await self.powerwall.get_sitemaster()

        self.assertIsInstance(sitemaster, SiteMasterResponse)

        sitemaster.status
        sitemaster.is_running
        sitemaster.is_connected_to_tesla
        sitemaster.is_power_supply_mode

    async def test_site_info(self) -> None:
        site_info = await self.powerwall.get_site_info()

        self.assertIsInstance(site_info, SiteInfoResponse)

        site_info.nominal_system_energy
        site_info.site_name
        site_info.timezone

    async def test_capacity(self) -> None:
        self.assertIsInstance(await self.powerwall.get_capacity(), int)

    async def test_energy(self) -> None:
        self.assertIsInstance(await self.powerwall.get_energy(), int)

    async def test_batteries(self) -> None:
        batteries = await self.powerwall.get_batteries()
        self.assertGreater(len(batteries), 0)
        for battery in batteries:
            battery.wobble_detected
            battery.energy_discharged
            battery.energy_charged
            battery.energy_remaining
            battery.capacity
            battery.part_number
            battery.serial_number

    async def test_grid_status(self) -> None:
        grid_status = await self.powerwall.get_grid_status()
        self.assertIsInstance(grid_status, GridStatus)

    async def test_status(self) -> None:
        status = await self.powerwall.get_status()
        self.assertIsInstance(status, PowerwallStatusResponse)
        status.up_time_seconds
        status.start_time
        status.version

    async def test_islanding(self) -> None:
        initial_grid_status = await self.powerwall.get_grid_status()
        self.assertIsInstance(initial_grid_status, GridStatus)

        if initial_grid_status == GridStatus.CONNECTED:
            await self.go_offline()
            await self.go_online()
        elif initial_grid_status == GridStatus.ISLANDED:
            await self.go_offline()
            await self.go_online()

    async def go_offline(self) -> None:
        observedIslandMode = await self.powerwall.set_island_mode(IslandMode.OFFGRID)
        self.assertEqual(observedIslandMode, IslandMode.OFFGRID)
        await self.wait_until_grid_status(GridStatus.ISLANDED)
        self.assertEqual(await self.powerwall.get_grid_status(), GridStatus.ISLANDED)

    async def go_online(self) -> None:
        observedIslandMode = await self.powerwall.set_island_mode(IslandMode.ONGRID)
        self.assertEqual(observedIslandMode, IslandMode.ONGRID)
        await self.wait_until_grid_status(GridStatus.CONNECTED)
        self.assertEqual(await self.powerwall.get_grid_status(), GridStatus.CONNECTED)

    async def wait_until_grid_status(
        self,
        expectedStatus: GridStatus,
        sleepTime: int = 1,
        maxCycles: int = 20,
    ) -> None:
        cycles = 0
        observedStatus: GridStatus

        while cycles < maxCycles:
            observedStatus = await self.powerwall.get_grid_status()
            if observedStatus == expectedStatus:
                break
            await asyncio.sleep(sleepTime)
            cycles = cycles + 1

        self.assertEqual(observedStatus, expectedStatus)
