import unittest
import json

import requests
import responses
from responses import add, Response, GET, POST

from tesla_powerwall import (
    Powerwall,
    AccessDeniedError,
    PowerwallUnreachableError,
    ApiError
)

ENDPOINT = "https://1.1.1.1/api/"


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
                GET,
                url=f'{ENDPOINT}system_status/soe',
                json={'percentage': 53}
            )
        )
        self.assertEqual(self.powerwall.charge, 53)

    @responses.activate
    def test_process_response(self):
        res = requests.Response()
        res.request = requests.Request(
            method="GET", url=f"{ENDPOINT}test").prepare()
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
        self.assertEqual(self.powerwall._process_response(
            res), {"response": "ok"})

    @responses.activate
    def test_get(self):
        add(
            Response(
                GET,
                url=f'{ENDPOINT}test_get',
                json={'test_get': True}
            )
        )

        self.assertEqual(self.powerwall._get('test_get'), {'test_get': True})

    @responses.activate
    def test_post(self):
        def post_callback(request):
            resp_body = {'test_post': True}
            headers = {}
            return (200, headers, json.dumps(resp_body))

        responses.add_callback(
            responses.POST,
            url=f'{ENDPOINT}test_post',
            callback=post_callback,
            content_type="application/json"
        )

        resp = self.powerwall._post(
            'test_post',
            {'test': True}
        )

        self.assertIsInstance(resp, dict)
        self.assertEqual(resp, {'test_post': True})