import json
import os
import unittest

import requests
import responses
from responses import GET, POST, Response, add

from tesla_powerwall import (
    AccessDeniedError,
    ApiError,
    MetersAggregateResponse,
    MetersResponse,
    MeterType,
    Powerwall,
    PowerwallUnreachableError,
)

ENDPOINT = "https://1.1.1.1/api/"

METERS_RESPONSE = {
    "site": {
        "last_communication_time": "2020-04-09T05:50:38.989687241-07:00",
        "instant_power": -5347.455078125,
        "instant_reactive_power": -664.1942901611328,
        "instant_apparent_power": 5388.546173843879,
        "frequency": 49.99971389770508,
        "energy_exported": 5512641.122754764,
        "energy_imported": 9852397.795532543,
        "instant_average_voltage": 232.0439249674479,
        "instant_total_current": 0,
        "i_a_current": 0,
        "i_b_current": 0,
        "i_c_current": 0,
        "timeout": 1500000000,
    },
    "battery": {
        "last_communication_time": "2020-04-09T05:50:38.990165237-07:00",
        "instant_power": -10,
        "instant_reactive_power": 600,
        "instant_apparent_power": 600.0833275470999,
        "frequency": 49.995000000000005,
        "energy_exported": 4379890,
        "energy_imported": 5265110,
        "instant_average_voltage": 230.8,
        "instant_total_current": -0.4,
        "i_a_current": 0,
        "i_b_current": 0,
        "i_c_current": 0,
        "timeout": 1500000000,
    },
    "load": {
        "last_communication_time": "2020-04-09T05:50:38.974944676-07:00",
        "instant_power": 734.1549565813606,
        "instant_reactive_power": -469.988307011022,
        "instant_apparent_power": 871.7066645380579,
        "frequency": 49.99971389770508,
        "energy_exported": 0,
        "energy_imported": 24751111.13611111,
        "instant_average_voltage": 232.0439249674479,
        "instant_total_current": 3.1638620001982423,
        "i_a_current": 0,
        "i_b_current": 0,
        "i_c_current": 0,
        "timeout": 1500000000,
    },
    "solar": {
        "last_communication_time": "2020-04-09T05:50:38.974944676-07:00",
        "instant_power": 6099.032958984375,
        "instant_reactive_power": -422.27491760253906,
        "instant_apparent_power": 6113.633873631454,
        "frequency": 49.95012283325195,
        "energy_exported": 21296639.987777833,
        "energy_imported": 65.52444450131091,
        "instant_average_voltage": 232.1537322998047,
        "instant_total_current": 0,
        "i_a_current": 0,
        "i_b_current": 0,
        "i_c_current": 0,
        "timeout": 1500000000,
    },
}

SITE_INFO_RESPONSE_WITHOUT_OPTIONS = {
    "max_site_meter_power_kW": 1000000000,
    "min_site_meter_power_kW": -1000000000,
    "nominal_system_energy_kWh": 13.5,
    "nominal_system_power_kW": 5,
    "max_system_energy_kWh": 0,
    "max_system_power_kW": 0,
    "site_name": "Test",
    "timezone": "Europe/Rome",
    "grid_code": "50Hz_230V_1_CEI-021:2016_Italy",
    "grid_voltage_setting": 230,
    "grid_freq_setting": 50,
    "grid_phase_setting": "Single",
    "country": "Italy",
    "state": "*",
    "region": "CEI-021",
}
SITE_INFO_RESPONSE_WITH_OPTIONS = {
    "max_site_meter_power_kW": 1000000000,
    "min_site_meter_power_kW": -1000000000,
    "nominal_system_energy_kWh": 13.5,
    "nominal_system_power_kW": 10,
    "max_system_energy_kWh": 0,
    "max_system_power_kW": 0,
    "site_name": "Test",
    "timezone": "Europe/Berlin",
    "grid_code": "50Hz_230V_1_VDE4105:2011_Germany",
    "grid_voltage_setting": 230,
    "grid_freq_setting": 50,
    "grid_phase_setting": "Single",
    "country": "Germany",
    "state": "*",
    "distributor": "*",
    "utility": "*",
    "retailer": "*",
    "region": "VDE4105",
}


class TestPowerWall(unittest.TestCase):
    def setUp(self):
        self.powerwall = Powerwall(ENDPOINT)

    def test_endpoint_setup(self):
        test_endpoint_1 = "1.1.1.1"
        pw = Powerwall(test_endpoint_1)
        self.assertEqual(pw._endpoint, f"https://{test_endpoint_1}/api/")

        test_endpoint_2 = "http://1.1.1.1"
        pw = Powerwall(test_endpoint_2)
        self.assertEqual(pw._endpoint, f"https://1.1.1.1/api/")

        test_endpoint_3 = "https://1.1.1.1/api/"
        pw = Powerwall(test_endpoint_3)
        self.assertEqual(pw._endpoint, test_endpoint_3)

    @responses.activate
    def test_get_charge(self):
        add(
            Response(
                GET, url=f"{ENDPOINT}system_status/soe", json={"percentage": 53.123423}
            )
        )
        self.assertEqual(self.powerwall.get_charge(), 53)
        self.assertEqual(self.powerwall.get_charge(rounded=False), 53.123423)

    @responses.activate
    def test_process_response(self):
        res = requests.Response()
        res.request = requests.Request(method="GET", url=f"{ENDPOINT}test").prepare()
        res.status_code = 401
        with self.assertRaises(AccessDeniedError):
            self.powerwall._process_response(res)

        res.status_code = 502
        with self.assertRaises(PowerwallUnreachableError):
            self.powerwall._process_response(res)

        res.status_code = 200
        res._content = b'{"error": "test_error"}'
        with self.assertRaises(ApiError):
            self.powerwall._process_response(res)

        res._content = b'{"response": "ok"}'
        self.assertEqual(self.powerwall._process_response(res), {"response": "ok"})

    @responses.activate
    def test_get(self):
        add(Response(GET, url=f"{ENDPOINT}test_get", json={"test_get": True}))

        self.assertEqual(self.powerwall._get("test_get"), {"test_get": True})

    @responses.activate
    def test_post(self):
        def post_callback(request):
            resp_body = {"test_post": True}
            headers = {}
            return (200, headers, json.dumps(resp_body))

        responses.add_callback(
            responses.POST,
            url=f"{ENDPOINT}test_post",
            callback=post_callback,
            content_type="application/json",
        )

        resp = self.powerwall._post("test_post", {"test": True})

        self.assertIsInstance(resp, dict)
        self.assertEqual(resp, {"test_post": True})

    @responses.activate
    def test_meters(self):
        add(
            Response(
                responses.GET, url=f"{ENDPOINT}meters/aggregates", json=METERS_RESPONSE
            )
        )
        meters = self.powerwall.get_meters()
        self.assertIsInstance(meters, MetersAggregateResponse)

        self.assertIsInstance(meters.site, MetersResponse)
        self.assertIsInstance(meters.solar, MetersResponse)
        self.assertIsInstance(meters.battery, MetersResponse)
        self.assertIsInstance(meters.load, MetersResponse)

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
    def test_optional_json_attrs(self):
        add(
            Response(
                responses.GET,
                url=f"{ENDPOINT}site_info",
                json=SITE_INFO_RESPONSE_WITHOUT_OPTIONS,
            )
        )

        add(
            Response(
                responses.GET,
                url=f"{ENDPOINT}site_info",
                json=SITE_INFO_RESPONSE_WITH_OPTIONS,
            )
        )

        site_info = self.powerwall.get_site_info()
        self.assertEqual(site_info.has_optional_attrs_set(), False)
        self.assertEqual(site_info.has_key("utility"), False)
        self.assertEqual(site_info.grid_voltage_setting, 230)
        self.assertEqual(site_info.has_optional_attrs(), True)

        site_info = self.powerwall.get_site_info()
        self.assertEqual(site_info.has_optional_attrs_set(), True)
        self.assertEqual(site_info.has_key("utility"), True)
        self.assertEqual(site_info.retailer, "*")
