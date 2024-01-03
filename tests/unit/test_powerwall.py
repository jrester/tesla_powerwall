import aiohttp
import aresponses
import datetime
import unittest
import json as jsonmod

from tesla_powerwall import (
    API,
    DeviceType,
    GridStatus,
    IslandMode,
    MeterDetailsReadings,
    MeterDetailsResponse,
    MeterNotAvailableError,
    MeterResponse,
    MetersAggregatesResponse,
    MeterType,
    MissingAttributeError,
    Powerwall,
    SiteMasterResponse,
    assert_attribute,
    convert_to_kw,
)
from tesla_powerwall.const import OperationMode
from tests.unit import (
    ENDPOINT_HOST,
    ENDPOINT_PATH,
    ENDPOINT,
    GRID_STATUS_RESPONSE,
    ISLANDING_MODE_OFFGRID_RESPONSE,
    ISLANDING_MODE_ONGRID_RESPONSE,
    METER_SITE_RESPONSE,
    METER_SOLAR_RESPONSE,
    METERS_AGGREGATES_RESPONSE,
    OPERATION_RESPONSE,
    POWERWALLS_RESPONSE,
    SITE_INFO_RESPONSE,
    SITEMASTER_RESPONSE,
    STATUS_RESPONSE,
    SYSTEM_STATUS_RESPONSE,
)


class TestPowerWall(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.aresponses = aresponses.ResponsesMockServer()
        self.session = aiohttp.ClientSession()

        await self.aresponses.__aenter__()
        await self.session.__aenter__()

        self.powerwall = Powerwall(ENDPOINT, http_session=self.session)

    async def asyncTearDown(self):
        await self.session.close()
        await self.session.__aexit__(None, None, None)
        await self.aresponses.__aexit__(None, None, None)

    def test_get_api(self):
        self.assertIsInstance(self.powerwall.get_api(), API)

    def add_response(self, path: str, method: str = "GET", json: object = None):
        self.aresponses.add(
            ENDPOINT_HOST,
            f"{ENDPOINT_PATH}{path}",
            method,
            self.aresponses.Response(
                headers={"Content-Type": "application/json"},
                text=jsonmod.dumps(json),
            ),
        )

    async def test_get_charge(self):
        self.add_response("system_status/soe", json={"percentage": 53.123423})
        self.assertEqual(await self.powerwall.get_charge(), 53.123423)
        self.aresponses.assert_plan_strictly_followed()

    async def test_get_sitemaster(self):
        self.add_response("sitemaster", json=SITEMASTER_RESPONSE)

        sitemaster = await self.powerwall.get_sitemaster()
        self.assertIsInstance(sitemaster, SiteMasterResponse)

        self.assertEqual(sitemaster.status, "StatusUp")
        self.assertEqual(sitemaster.is_running, True)
        self.assertEqual(sitemaster.is_connected_to_tesla, True)
        self.assertEqual(sitemaster.is_power_supply_mode, False)
        self.aresponses.assert_plan_strictly_followed()

    async def test_get_meters(self):
        self.add_response("meters/aggregates", json=METERS_AGGREGATES_RESPONSE)
        meters = await self.powerwall.get_meters()
        self.assertIsInstance(meters, MetersAggregatesResponse)
        self.assertListEqual(
            list(meters.meters.keys()),
            [
                MeterType.BATTERY,
                MeterType.LOAD,
                MeterType.SITE,
                MeterType.SOLAR,
            ],
        )
        self.assertIsInstance(meters.load, MeterResponse)
        self.assertIsInstance(meters.get_meter(MeterType.LOAD), MeterResponse)
        self.assertIsNone(meters.get_meter(MeterType.GENERATOR))
        with self.assertRaises(MeterNotAvailableError):
            meters.generator
        self.aresponses.assert_plan_strictly_followed()

    async def test_get_meter_site(self):
        self.add_response("meters/site", json=METER_SITE_RESPONSE)
        meter = await self.powerwall.get_meter_site()
        self.assertIsInstance(meter, MeterDetailsResponse)
        self.assertEqual(meter.location, MeterType.SITE)
        readings = meter.readings
        self.assertIsInstance(readings, MeterDetailsReadings)
        # Optional voltage fields
        self.assertIsInstance(readings.v_l1n, float)
        self.assertIsInstance(readings.v_l2n, float)
        self.assertIsNone(readings.v_l3n)

        self.assertEqual(readings.instant_power, -18.00000076368451)
        self.assertEqual(readings.get_power(), -0.0)
        self.aresponses.assert_plan_strictly_followed()

    async def test_get_meter_solar(self):
        self.add_response("meters/solar", json=METER_SOLAR_RESPONSE)
        meter = await self.powerwall.get_meter_solar()
        self.assertIsInstance(meter, MeterDetailsResponse)
        self.assertEqual(meter.location, MeterType.SOLAR)
        readings = meter.readings
        self.assertIsInstance(readings, MeterDetailsReadings)
        # Optional voltage fields
        self.assertIsInstance(readings.v_l1n, float)
        self.assertIsNone(readings.v_l2n)
        self.assertIsNone(readings.v_l3n)
        self.aresponses.assert_plan_strictly_followed()

    async def test_is_sending(self):
        self.add_response("meters/aggregates", json=METERS_AGGREGATES_RESPONSE)
        meters = await self.powerwall.get_meters()
        self.assertEqual(meters.get_meter(MeterType.SOLAR).is_sending_to(), False)
        self.assertEqual(meters.get_meter(MeterType.SOLAR).is_active(), True)
        self.assertEqual(meters.get_meter(MeterType.SOLAR).is_drawing_from(), True)
        self.assertEqual(meters.get_meter(MeterType.SITE).is_sending_to(), True)
        self.assertEqual(meters.get_meter(MeterType.LOAD).is_sending_to(), True)
        self.assertEqual(meters.get_meter(MeterType.LOAD).is_drawing_from(), False)
        self.assertEqual(meters.get_meter(MeterType.LOAD).is_active(), True)
        self.aresponses.assert_plan_strictly_followed()

    async def test_get_grid_status(self):
        self.add_response("system_status/grid_status", json=GRID_STATUS_RESPONSE)
        grid_status = await self.powerwall.get_grid_status()
        self.assertEqual(grid_status, GridStatus.CONNECTED)
        self.aresponses.assert_plan_strictly_followed()

    async def test_is_grid_services_active(self):
        self.add_response("system_status/grid_status", json=GRID_STATUS_RESPONSE)
        self.assertEqual(await self.powerwall.is_grid_services_active(), False)
        self.aresponses.assert_plan_strictly_followed()

    async def test_get_site_info(self):
        self.add_response("site_info", json=SITE_INFO_RESPONSE)
        site_info = await self.powerwall.get_site_info()
        self.assertEqual(site_info.nominal_system_energy, 27)
        self.assertEqual(site_info.site_name, "test")
        self.assertEqual(site_info.timezone, "Europe/Berlin")
        self.aresponses.assert_plan_strictly_followed()

    async def test_get_status(self):
        self.add_response("status", json=STATUS_RESPONSE)
        status = await self.powerwall.get_status()
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
        self.aresponses.assert_plan_strictly_followed()

    async def test_get_device_type(self):
        self.add_response("status", json=STATUS_RESPONSE)
        device_type = await self.powerwall.get_device_type()
        self.assertIsInstance(device_type, DeviceType)
        self.assertEqual(device_type, DeviceType.GW1)
        self.aresponses.assert_plan_strictly_followed()

    async def test_get_serial_numbers(self):
        self.add_response("powerwalls", json=POWERWALLS_RESPONSE)
        serial_numbers = await self.powerwall.get_serial_numbers()
        self.assertEqual(serial_numbers, ["SerialNumber1", "SerialNumber2"])
        self.aresponses.assert_plan_strictly_followed()

    async def test_get_gateway_din(self):
        self.add_response("powerwalls", json=POWERWALLS_RESPONSE)
        gateway_din = await self.powerwall.get_gateway_din()
        self.assertEqual(gateway_din, "gateway_din")
        self.aresponses.assert_plan_strictly_followed()

    async def test_get_backup_reserved_percentage(self):
        self.add_response("operation", json=OPERATION_RESPONSE)
        self.assertEqual(
            await self.powerwall.get_backup_reserve_percentage(), 5.000019999999999
        )
        self.aresponses.assert_plan_strictly_followed()

    async def test_get_operation_mode(self):
        self.add_response("operation", json=OPERATION_RESPONSE)
        self.assertEqual(
            await self.powerwall.get_operation_mode(), OperationMode.SELF_CONSUMPTION
        )
        self.aresponses.assert_plan_strictly_followed()

    async def test_get_version(self):
        self.add_response("status", json=STATUS_RESPONSE)
        self.assertEqual(await self.powerwall.get_version(), "1.50.1")
        self.aresponses.assert_plan_strictly_followed()

    async def test_system_status(self):
        self.add_response("system_status", json=SYSTEM_STATUS_RESPONSE)
        self.assertEqual(await self.powerwall.get_capacity(), 28078)

        self.add_response("system_status", json=SYSTEM_STATUS_RESPONSE)
        self.assertEqual(await self.powerwall.get_energy(), 14807)

        self.add_response("system_status", json=SYSTEM_STATUS_RESPONSE)
        batteries = await self.powerwall.get_batteries()
        self.assertEqual(len(batteries), 2)
        self.assertEqual(batteries[0].part_number, "XXX-G")
        self.assertEqual(batteries[0].serial_number, "TGXXX")
        self.assertEqual(batteries[0].energy_remaining, 7378)
        self.assertEqual(batteries[0].capacity, 14031)
        self.assertEqual(batteries[0].energy_charged, 5525740)
        self.assertEqual(batteries[0].energy_discharged, 4659550)
        self.assertEqual(batteries[0].wobble_detected, False)
        self.aresponses.assert_plan_strictly_followed()

    async def test_islanding_mode_offgrid(self):
        self.add_response(
            "v2/islanding/mode", method="POST", json=ISLANDING_MODE_OFFGRID_RESPONSE
        )

        mode = await self.powerwall.set_island_mode(IslandMode.OFFGRID)
        self.assertEqual(mode, IslandMode.OFFGRID)
        self.aresponses.assert_plan_strictly_followed()

    async def test_islanding_mode_ongrid(self):
        self.add_response(
            "v2/islanding/mode", method="POST", json=ISLANDING_MODE_ONGRID_RESPONSE
        )

        mode = await self.powerwall.set_island_mode(IslandMode.ONGRID)
        self.assertEqual(mode, IslandMode.ONGRID)
        self.aresponses.assert_plan_strictly_followed()

    def test_helpers(self):
        resp = {"a": 1}
        with self.assertRaises(MissingAttributeError):
            assert_attribute(resp, "test")

        with self.assertRaises(MissingAttributeError):
            assert_attribute(resp, "test", "test")

        self.assertEqual(convert_to_kw(2500, -1), 2.5)
