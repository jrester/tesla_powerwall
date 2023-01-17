import datetime
import unittest

import responses
from responses import GET, Response, add

from tesla_powerwall import (
    API,
    DeviceType,
    GridStatus,
    IslandMode,
    Meter,
    MeterNotAvailableError,
    MetersAggregates,
    MeterType,
    MissingAttributeError,
    Powerwall,
    SiteMaster,
    assert_attribute,
    convert_to_kw,
)
from tesla_powerwall.const import OperationMode
from tests.unit import (
    ENDPOINT,
    GRID_STATUS_RESPONSE,
    METERS_AGGREGATES_RESPONSE,
    OPERATION_RESPONSE,
    POWERWALLS_RESPONSE,
    SITE_INFO_RESPONSE,
    SITEMASTER_RESPONSE,
    STATUS_RESPONSE,
    SYSTEM_STATUS_RESPONSE,
    ISLANDING_MODE_ONGRID_RESPONSE,
    ISLANDING_MODE_OFFGRID_RESPONSE,
)


class TestPowerWall(unittest.TestCase):
    def setUp(self):
        self.powerwall = Powerwall(ENDPOINT)

    def test_get_api(self):
        self.assertIsInstance(self.powerwall.get_api(), API)

    @responses.activate
    def test_get_charge(self):
        add(
            Response(
                GET, url=f"{ENDPOINT}system_status/soe", json={"percentage": 53.123423}
            )
        )
        self.assertEqual(self.powerwall.get_charge(), 53.123423)

    @responses.activate
    def test_get_sitemaster(self):
        add(
            Response(
                responses.GET, url=f"{ENDPOINT}sitemaster", json=SITEMASTER_RESPONSE
            )
        )

        sitemaster = self.powerwall.get_sitemaster()
        self.assertIsInstance(sitemaster, SiteMaster)

        self.assertEqual(sitemaster.status, "StatusUp")
        self.assertEqual(sitemaster.is_running, True)
        self.assertEqual(sitemaster.is_connected_to_tesla, True)
        self.assertEqual(sitemaster.is_power_supply_mode, False)

    @responses.activate
    def test_get_meters(self):
        add(
            Response(
                responses.GET,
                url=f"{ENDPOINT}meters/aggregates",
                json=METERS_AGGREGATES_RESPONSE,
            )
        )
        meters = self.powerwall.get_meters()
        self.assertIsInstance(meters, MetersAggregates)
        self.assertListEqual(
            meters.meters,
            [MeterType.SITE, MeterType.BATTERY, MeterType.LOAD, MeterType.SOLAR],
        )
        self.assertIsInstance(meters.load, Meter)
        self.assertIsInstance(meters.get_meter(MeterType.LOAD), Meter)
        with self.assertRaises(MeterNotAvailableError):
            meters.generator

    @responses.activate
    def test_is_sending(self):
        add(
            Response(
                responses.GET,
                url=f"{ENDPOINT}meters/aggregates",
                json=METERS_AGGREGATES_RESPONSE,
            )
        )
        meters = self.powerwall.get_meters()
        self.assertEqual(meters.get_meter(MeterType.SOLAR).is_sending_to(), False)
        self.assertEqual(meters.get_meter(MeterType.SOLAR).is_active(), True)
        self.assertEqual(meters.get_meter(MeterType.SOLAR).is_drawing_from(), True)
        self.assertEqual(meters.get_meter(MeterType.SITE).is_sending_to(), True)
        self.assertEqual(meters.get_meter(MeterType.LOAD).is_sending_to(), True)
        self.assertEqual(meters.get_meter(MeterType.LOAD).is_drawing_from(), False)
        self.assertEqual(meters.get_meter(MeterType.LOAD).is_active(), True)

    @responses.activate
    def test_get_grid_status(self):
        add(
            Response(
                responses.GET,
                url=f"{ENDPOINT}system_status/grid_status",
                json=GRID_STATUS_RESPONSE,
            )
        )
        grid_status = self.powerwall.get_grid_status()
        self.assertEqual(grid_status, GridStatus.CONNECTED)

    @responses.activate
    def test_is_grid_services_active(self):
        add(
            Response(
                responses.GET,
                url=f"{ENDPOINT}system_status/grid_status",
                json=GRID_STATUS_RESPONSE,
            )
        )
        self.assertEqual(self.powerwall.is_grid_services_active(), False)

    @responses.activate
    def test_get_site_info(self):
        add(
            Response(responses.GET, url=f"{ENDPOINT}site_info", json=SITE_INFO_RESPONSE)
        )
        site_info = self.powerwall.get_site_info()
        self.assertEqual(site_info.nominal_system_energy, 27)
        self.assertEqual(site_info.site_name, "test")
        self.assertEqual(site_info.timezone, "Europe/Berlin")

    @responses.activate
    def test_get_status(self):
        add(Response(responses.GET, url=f"{ENDPOINT}status", json=STATUS_RESPONSE))
        status = self.powerwall.get_status()
        self.assertEqual(
            status.up_time_seconds,
            datetime.timedelta(seconds=61891, microseconds=214751),
        )
        self.assertEqual(
            status.start_time,
            datetime.datetime(
                2020,
                10,
                28,
                20,
                14,
                11,
                tzinfo=datetime.timezone(datetime.timedelta(seconds=28800)),
            ),
        )
        self.assertEqual(status.device_type, DeviceType.GW1)
        self.assertEqual(status.version, "1.50.1 c58c2df3")

    @responses.activate
    def test_get_device_type(self):
        add(Response(responses.GET, url=f"{ENDPOINT}status", json=STATUS_RESPONSE))
        device_type = self.powerwall.get_device_type()
        self.assertIsInstance(device_type, DeviceType)
        self.assertEqual(device_type, DeviceType.GW1)

    @responses.activate
    def test_get_serial_numbers(self):
        add(
            Response(
                responses.GET, url=f"{ENDPOINT}powerwalls", json=POWERWALLS_RESPONSE
            )
        )
        serial_numbers = self.powerwall.get_serial_numbers()
        self.assertEqual(serial_numbers, ["SerialNumber1", "SerialNumber2"])

    @responses.activate
    def test_get_gateway_din(self):
        add(
            Response(
                responses.GET, url=f"{ENDPOINT}powerwalls", json=POWERWALLS_RESPONSE
            )
        )
        gateway_din = self.powerwall.get_gateway_din()
        self.assertEqual(gateway_din, "gateway_din")

    @responses.activate
    def test_get_backup_reserved_percentage(self):
        add(
            Response(responses.GET, url=f"{ENDPOINT}operation", json=OPERATION_RESPONSE)
        )
        self.assertEqual(
            self.powerwall.get_backup_reserve_percentage(), 5.000019999999999
        )

    @responses.activate
    def test_get_operation_mode(self):
        add(
            Response(responses.GET, url=f"{ENDPOINT}operation", json=OPERATION_RESPONSE)
        )
        self.assertEqual(
            self.powerwall.get_operation_mode(), OperationMode.SELF_CONSUMPTION
        )

    @responses.activate
    def test_get_version(self):
        add(Response(responses.GET, url=f"{ENDPOINT}status", json=STATUS_RESPONSE))
        self.assertEqual(self.powerwall.get_version(), "1.50.1")

    @responses.activate
    def test_system_status(self):
        add(
            Response(
                responses.GET,
                url=f"{ENDPOINT}system_status",
                json=SYSTEM_STATUS_RESPONSE,
            )
        )
        self.assertEqual(self.powerwall.get_capacity(), 28078)
        self.assertEqual(self.powerwall.get_energy(), 14807)

        batteries = self.powerwall.get_batteries()
        self.assertEqual(len(batteries), 2)
        self.assertEqual(batteries[0].part_number, "XXX-G")
        self.assertEqual(batteries[0].serial_number, "TGXXX")
        self.assertEqual(batteries[0].energy_remaining, 7378)
        self.assertEqual(batteries[0].capacity, 14031)
        self.assertEqual(batteries[0].energy_charged, 5525740)
        self.assertEqual(batteries[0].energy_discharged, 4659550)
        self.assertEqual(batteries[0].wobble_detected, False)

    @responses.activate
    def test_islanding_mode_offgrid(self):
        add(
            Response(
                responses.POST,
                url=f"{ENDPOINT}v2/islanding/mode",
                json=ISLANDING_MODE_OFFGRID_RESPONSE,
            )
        )
        
        mode = self.powerwall.set_island_mode(IslandMode.OFFGRID)
        self.assertEqual(mode, IslandMode.OFFGRID)

    @responses.activate
    def test_islanding_mode_ongrid(self):
        add(
            Response(
                responses.POST,
                url=f"{ENDPOINT}v2/islanding/mode",
                json=ISLANDING_MODE_ONGRID_RESPONSE,
            )
        )
        
        mode = self.powerwall.set_island_mode(IslandMode.ONGRID)
        self.assertEqual(mode, IslandMode.ONGRID)

    def test_helpers(self):
        resp = {"a": 1}
        with self.assertRaises(MissingAttributeError):
            assert_attribute(resp, "test")

        with self.assertRaises(MissingAttributeError):
            assert_attribute(resp, "test", "test")

        self.assertEqual(convert_to_kw(2500, -1), 2.5)
