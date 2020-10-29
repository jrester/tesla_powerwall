import json
import os
import unittest
import datetime

from packaging import version
import requests
import responses
from responses import GET, POST, Response, add

from tesla_powerwall import (
    API,
    AccessDeniedError,
    APIError,
    Meter,
    MetersAggregates,
    Powerwall,
    PowerwallUnreachableError,
    SiteMaster,
    SiteInfo,
    GridStatus,
    DeviceType,
    assert_attribute,
    convert_to_kw,
    MissingAttributeError,
    MeterType
)

from . import ENDPOINT, METERS_RESPONSE, STATUS_RESPONSE, GRID_STATUS_RESPONSE, SITE_INFO_RESPONSE, POWERWALLS_RESPONSE, SITE_MASTER_RESPONSE, OPERATION_RESPONSE

class TestPowerWall(unittest.TestCase):
    def setUp(self):
        self.powerwall = Powerwall(ENDPOINT)

    def test_get_api(self):
        self.assertIsInstance(self.powerwall.get_api(), API)

    def test_pins_version_on_creation(self):
        pw = Powerwall(ENDPOINT, pin_version="1.49.0")
        self.assertEqual(pw.get_pinned_version(), version.parse("1.49.0"))

        pw = Powerwall(ENDPOINT, pin_version=version.parse("1.49.0"))
        self.assertEqual(pw.get_pinned_version(), version.parse("1.49.0"))

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
                responses.GET, url=f"{ENDPOINT}sitemaster", json=SITE_MASTER_RESPONSE
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
                responses.GET, url=f"{ENDPOINT}meters/aggregates", json=METERS_RESPONSE
            )
        )
        meters = self.powerwall.get_meters()
        self.assertIsInstance(meters, MetersAggregates)

        self.assertIsInstance(meters.site, Meter)
        self.assertIsInstance(meters.solar, Meter)
        self.assertIsInstance(meters.battery, Meter)
        self.assertIsInstance(meters.load, Meter)
        self.assertIsInstance(meters.get_meter(MeterType.SOLAR), Meter)

    @responses.activate
    def test_meter(self):
        add(
            Response(
                responses.GET, url=f"{ENDPOINT}meters/aggregates", json=METERS_RESPONSE
            )
        )

    @responses.activate
    def test_is_sending(self):
        add(
            Response(
                responses.GET, url=f"{ENDPOINT}meters/aggregates", json=METERS_RESPONSE
            )
        )
        meters = self.powerwall.get_meters()
        self.assertEqual(meters.solar.is_sending_to(), False)
        self.assertEqual(meters.solar.is_active(), True)
        self.assertEqual(meters.solar.is_drawing_from(), True)
        self.assertEqual(meters.site.is_sending_to(), True)
        self.assertEqual(meters.load.is_sending_to(), True)
        self.assertEqual(meters.load.is_drawing_from(), False)
        self.assertEqual(meters.load.is_active(), True)



    @responses.activate
    def test_get_grid_status(self):
        add(
            Response(
                responses.GET, url=f"{ENDPOINT}system_status/grid_status", json=GRID_STATUS_RESPONSE
            )
        )
        grid_status = self.powerwall.get_grid_status()
        self.assertEqual(grid_status, GridStatus.CONNECTED)

    @responses.activate
    def test_is_grid_services_active(self):
        add(
            Response(
                responses.GET, url=f"{ENDPOINT}system_status/grid_status", json=GRID_STATUS_RESPONSE
            )
        )
        self.assertEqual(self.powerwall.is_grid_services_active(), False)

    @responses.activate
    def test_get_site_info(self):
        add(
            Response(
                responses.GET, url=f"{ENDPOINT}site_info", json=SITE_INFO_RESPONSE
            )
        )
        site_info = self.powerwall.get_site_info()
        self.assertEqual(site_info.nominal_system_energy, 27)
        self.assertEqual(site_info.site_name, "test")
        self.assertEqual(site_info.timezone, "Europe/Berlin")

    @responses.activate
    def test_get_status(self):
        add(
            Response(
                responses.GET, url=f"{ENDPOINT}status", json=STATUS_RESPONSE
            )
        )
        status = self.powerwall.get_status()
        self.assertEqual(status.up_time_seconds, datetime.timedelta(seconds=62105, microseconds=751424))
        self.assertEqual(status.start_time, datetime.datetime(2020, 10, 28, 20, 14, 11, tzinfo=datetime.timezone(datetime.timedelta(seconds=28800))))
        self.assertEqual(status.device_type, DeviceType.GW1)
        self.assertEqual(status.version, "1.50.1")

    @responses.activate
    def test_get_device_type(self):
        add(
            Response(
                responses.GET, url=f"{ENDPOINT}status", json=STATUS_RESPONSE
            )
        )
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
    def test_get_backup_reserved_percentage(self):
        add(
            Response(
                responses.GET, url=f"{ENDPOINT}operation", json=OPERATION_RESPONSE
            )
        )

    @responses.activate
    def test_get_operation_mode(self):
        add(
            Response(
                responses.GET, url=f"{ENDPOINT}operation", json=OPERATION_RESPONSE
            )
        )

    @responses.activate
    def test_get_version(self):
        add(
            Response(
                responses.GET, url=f"{ENDPOINT}status", json=STATUS_RESPONSE
            )
        )
        self.assertEqual(self.powerwall.get_version(), "1.50.1")

    @responses.activate
    def test_detect_and_pin_version(self):
        add(
            Response(
                responses.GET, url=f"{ENDPOINT}status", json=STATUS_RESPONSE
            )
        )
        vers = version.parse("1.50.1")
        pw = Powerwall(ENDPOINT)
        self.assertEqual(pw.detect_and_pin_version(), vers)
        self.assertEqual(pw._pin_version, vers)

    def test_helpers(self):
        resp = {"a": 1}
        with self.assertRaises(MissingAttributeError):
            assert_attribute(resp, "test")

        with self.assertRaises(MissingAttributeError):
            assert_attribute(resp, "test", "test")

        self.assertEqual(convert_to_kw(2500, -1), 2.5)

    def test_misc(self):
        PowerwallUnreachableError("reason")
        AccessDeniedError("test", "Error reason")
