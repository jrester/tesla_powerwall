import unittest
from time import sleep

from tesla_powerwall import (
    GridStatus,
    IslandMode,
    Meter,
    MetersAggregates,
    MeterType,
    Powerwall,
    SiteInfo,
    SiteMaster,
)
from tesla_powerwall.responses import PowerwallStatus
from tests.integration import POWERWALL_IP, POWERWALL_PASSWORD


class TestPowerwall(unittest.TestCase):
    def setUp(self) -> None:
        self.powerwall = Powerwall(POWERWALL_IP)
        self.powerwall.login(POWERWALL_PASSWORD)

    def tearDown(self) -> None:
        self.powerwall.close()

    def test_get_charge(self) -> None:
        charge = self.powerwall.get_charge()
        if(charge < 100):
            self.assertIsInstance(charge, float)
        else:
            self.assertEqual(charge, 100)

    def test_get_meters(self) -> None:
        meters = self.powerwall.get_meters()
        self.assertIsInstance(meters, MetersAggregates)

        self.assertIsInstance(meters.get_meter(MeterType.BATTERY), Meter)

        for meter_type in meters.meters:
            meter = meters.get_meter(meter_type)
            meter.energy_exported
            meter.energy_imported
            meter.instant_power
            meter.last_communication_time
            meter.frequency
            meter.average_voltage
            meter.get_energy_exported()
            meter.get_energy_imported()
            self.assertIsInstance(meter.get_power(), float)
            self.assertIsInstance(meter.is_active(), bool)
            self.assertIsInstance(meter.is_drawing_from(), bool)
            self.assertIsInstance(meter.is_sending_to(), bool)

    def test_sitemaster(self) -> None:
        sitemaster = self.powerwall.get_sitemaster()

        self.assertIsInstance(sitemaster, SiteMaster)

        sitemaster.status
        sitemaster.is_running
        sitemaster.is_connected_to_tesla
        sitemaster.is_power_supply_mode

    def test_site_info(self) -> None:
        site_info = self.powerwall.get_site_info()

        self.assertIsInstance(site_info, SiteInfo)

        site_info.nominal_system_energy
        site_info.site_name
        site_info.timezone

    def test_capacity(self) -> None:
        self.assertIsInstance(self.powerwall.get_capacity(), int)

    def test_energy(self) -> None:
        self.assertIsInstance(self.powerwall.get_energy(), int)

    def test_batteries(self) -> None:
        batteries = self.powerwall.get_batteries()
        self.assertGreater(len(batteries), 0)
        for battery in batteries:
            battery.wobble_detected
            battery.energy_discharged
            battery.energy_charged
            battery.energy_remaining
            battery.capacity
            battery.part_number
            battery.serial_number

    def test_grid_status(self) -> None:
        grid_status = self.powerwall.get_grid_status()
        self.assertIsInstance(grid_status, GridStatus)

    def test_status(self) -> None:
        status = self.powerwall.get_status()
        self.assertIsInstance(status, PowerwallStatus)
        status.up_time_seconds
        status.start_time
        status.version

    def test_islanding(self) -> None:
        initial_grid_status = self.powerwall.get_grid_status()
        self.assertIsInstance(initial_grid_status, GridStatus)

        if(initial_grid_status == GridStatus.CONNECTED):
            self.go_offline()
            self.go_online()
        elif(initial_grid_status == GridStatus.ISLANDED):
            self.go_offline()
            self.go_online()

    def go_offline(self) -> None:
        observedIslandMode = self.powerwall.set_island_mode(IslandMode.OFFGRID)
        self.assertEqual(observedIslandMode, IslandMode.OFFGRID)
        self.wait_until_grid_status(GridStatus.ISLANDED)
        self.assertEqual(self.powerwall.get_grid_status(), GridStatus.ISLANDED)

    def go_online(self) -> None:
        observedIslandMode = self.powerwall.set_island_mode(IslandMode.ONGRID)
        self.assertEqual(observedIslandMode, IslandMode.ONGRID)
        self.wait_until_grid_status(GridStatus.CONNECTED)
        self.assertEqual(self.powerwall.get_grid_status(), GridStatus.CONNECTED)

    def wait_until_grid_status(self, expectedStatus: GridStatus, sleepTime: int = 1, maxCycles: int = 20) -> None:
        cycles = 0
        observedStatus: GridStatus

        while cycles < maxCycles:
            observedStatus = self.powerwall.get_grid_status()
            if(observedStatus == expectedStatus):
                break
            sleep(sleepTime)
            cycles = cycles + 1

        self.assertEqual(observedStatus, expectedStatus)
