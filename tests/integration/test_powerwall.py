from tesla_powerwall.responses import PowerwallStatus
import unittest

from tesla_powerwall import (
    Powerwall,
    GridStatus,
    SiteInfo,
    SiteMaster,
    MetersAggregates,
    Meter,
    MeterType,
    powerwall,
)

from tests.integration import POWERWALL_IP, POWERWALL_PASSWORD


class TestPowerwall(unittest.TestCase):
    def setUp(self) -> None:
        self.powerwall = Powerwall(POWERWALL_IP)
        self.powerwall.login(POWERWALL_PASSWORD)

    def tearDown(self) -> None:
        self.powerwall.close()

    def test_get_charge(self) -> None:
        charge = self.powerwall.get_charge()
        self.assertIsInstance(charge, float)

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

    def get_grid_status(self) -> None:
        grid_status = self.powerwall.get_grid_status()
        self.assertIsInstance(grid_status, GridStatus)

    def get_status(self) -> None:
        status = self.powerwall.get_status()
        self.assertIsInstance(status, PowerwallStatus)
        status.up_time_seconds
        status.start_time
        status.version
