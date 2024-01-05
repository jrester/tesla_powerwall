import aiohttp
import aresponses
import datetime
import json
from typing import Optional, Union
import unittest

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
        await self.aresponses.__aenter__()

        # Allow unsafe cookies so that folks can use IP addresses in their configs
        # See: https://docs.aiohttp.org/en/v3.7.3/client_advanced.html#cookie-safety
        jar = aiohttp.CookieJar(unsafe=True)
        self.session = aiohttp.ClientSession(cookie_jar=jar)
        self.powerwall = Powerwall(ENDPOINT)

    async def asyncTearDown(self):
        await self.powerwall.close()
        await self.session.close()
        await self.aresponses.__aexit__(None, None, None)

    def test_get_api(self):
        self.assertIsInstance(self.powerwall.get_api(), API)

    def add_response(
        self,
        path: str,
        method: str = "GET",
        content_type: str = "application/json",
        body: Optional[Union[str, dict]] = None,
    ):
        self.aresponses.add(
            ENDPOINT_HOST,
            f"{ENDPOINT_PATH}{path}",
            method,
            self.aresponses.Response(
                headers={"Content-Type": content_type},
                text=json.dumps(body),
            ),
        )

    async def test_get_charge(self):
        self.add_response("system_status/soe", body={"percentage": 53.123423})
        self.assertEqual(await self.powerwall.get_charge(), 53.123423)
        self.aresponses.assert_plan_strictly_followed()

    async def test_get_sitemaster(self):
        self.add_response("sitemaster", body=SITEMASTER_RESPONSE)

        sitemaster = await self.powerwall.get_sitemaster()
        self.assertIsInstance(sitemaster, SiteMasterResponse)

        self.assertEqual(sitemaster.status, "StatusUp")
        self.assertEqual(sitemaster.is_running, True)
        self.assertEqual(sitemaster.is_connected_to_tesla, True)
        self.assertEqual(sitemaster.is_power_supply_mode, False)
        self.aresponses.assert_plan_strictly_followed()

    async def test_get_meters(self):
        self.add_response("meters/aggregates", body=METERS_AGGREGATES_RESPONSE)
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
        self.add_response("meters/site", body=METER_SITE_RESPONSE)
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
        self.add_response("meters/solar", body=METER_SOLAR_RESPONSE)
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
        self.add_response("meters/aggregates", body=METERS_AGGREGATES_RESPONSE)
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
        self.add_response("system_status/grid_status", body=GRID_STATUS_RESPONSE)
        grid_status = await self.powerwall.get_grid_status()
        self.assertEqual(grid_status, GridStatus.CONNECTED)
        self.aresponses.assert_plan_strictly_followed()

    async def test_is_grid_services_active(self):
        self.add_response("system_status/grid_status", body=GRID_STATUS_RESPONSE)
        self.assertEqual(await self.powerwall.is_grid_services_active(), False)
        self.aresponses.assert_plan_strictly_followed()

    async def test_get_site_info(self):
        self.add_response("site_info", body=SITE_INFO_RESPONSE)
        site_info = await self.powerwall.get_site_info()
        self.assertEqual(site_info.nominal_system_energy, 27)
        self.assertEqual(site_info.site_name, "test")
        self.assertEqual(site_info.timezone, "Europe/Berlin")
        self.aresponses.assert_plan_strictly_followed()

    async def test_get_status(self):
        self.add_response("status", body=STATUS_RESPONSE)
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
        self.add_response("status", body=STATUS_RESPONSE)
        device_type = await self.powerwall.get_device_type()
        self.assertIsInstance(device_type, DeviceType)
        self.assertEqual(device_type, DeviceType.GW1)
        self.aresponses.assert_plan_strictly_followed()

    async def test_get_serial_numbers(self):
        self.add_response("powerwalls", body=POWERWALLS_RESPONSE)
        serial_numbers = await self.powerwall.get_serial_numbers()
        self.assertEqual(serial_numbers, ["SerialNumber1", "SerialNumber2"])
        self.aresponses.assert_plan_strictly_followed()

    async def test_get_gateway_din(self):
        self.add_response("powerwalls", body=POWERWALLS_RESPONSE)
        gateway_din = await self.powerwall.get_gateway_din()
        self.assertEqual(gateway_din, "gateway_din")
        self.aresponses.assert_plan_strictly_followed()

    async def test_get_backup_reserved_percentage(self):
        self.add_response("operation", body=OPERATION_RESPONSE)
        self.assertEqual(
            await self.powerwall.get_backup_reserve_percentage(), 5.000019999999999
        )
        self.aresponses.assert_plan_strictly_followed()

    async def test_get_operation_mode(self):
        self.add_response("operation", body=OPERATION_RESPONSE)
        self.assertEqual(
            await self.powerwall.get_operation_mode(), OperationMode.SELF_CONSUMPTION
        )
        self.aresponses.assert_plan_strictly_followed()

    async def test_get_version(self):
        self.add_response("status", body=STATUS_RESPONSE)
        self.assertEqual(await self.powerwall.get_version(), "1.50.1")
        self.aresponses.assert_plan_strictly_followed()

    async def test_system_status(self):
        self.add_response("system_status", body=SYSTEM_STATUS_RESPONSE)
        self.assertEqual(await self.powerwall.get_capacity(), 28078)

        self.add_response("system_status", body=SYSTEM_STATUS_RESPONSE)
        self.assertEqual(await self.powerwall.get_energy(), 14807)

        self.add_response("system_status", body=SYSTEM_STATUS_RESPONSE)
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
            "v2/islanding/mode", method="POST", body=ISLANDING_MODE_OFFGRID_RESPONSE
        )

        mode = await self.powerwall.set_island_mode(IslandMode.OFFGRID)
        self.assertEqual(mode, IslandMode.OFFGRID)
        self.aresponses.assert_plan_strictly_followed()

    async def test_islanding_mode_ongrid(self):
        self.add_response(
            "v2/islanding/mode", method="POST", body=ISLANDING_MODE_ONGRID_RESPONSE
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

    async def test_close(self):
        api_session = None
        async with Powerwall(ENDPOINT) as powerwall:
            api_session = powerwall._api._http_session
            self.assertFalse(api_session.closed)
        self.assertTrue(api_session.closed)

        async with aiohttp.ClientSession() as session:
            api_session = session
            async with Powerwall(ENDPOINT, http_session=session) as powerwall:
                self.assertFalse(api_session.closed)
            self.assertFalse(api_session.closed)
        self.assertTrue(api_session.closed)

        powerwall = Powerwall(ENDPOINT)
        api_session = powerwall._api._http_session
        self.assertFalse(api_session.closed)
        await powerwall.close()
        self.assertTrue(api_session.closed)

        async with aiohttp.ClientSession() as session:
            api_session = session
            powerwall = Powerwall(ENDPOINT, http_session=session)
            self.assertFalse(api_session.closed)
            await powerwall.close()
            self.assertFalse(api_session.closed)
        self.assertTrue(api_session.closed)
