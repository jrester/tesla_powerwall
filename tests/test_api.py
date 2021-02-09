import unittest
import json

import requests
import responses
from responses import GET, POST, Response, add

from tesla_powerwall import (
    API,
    AccessDeniedError,
    PowerwallUnreachableError,
    APIError
)

from . import ENDPOINT

class TestAPI(unittest.TestCase):
    def setUp(self):
        self.api = API(ENDPOINT)

    def test_parse_endpoint(self):
        test_endpoints = ["1.1.1.1", "http://1.1.1.1", "https://1.1.1.1/api/", "https://1.1.1.1/api", "https://1.1.1.1/"]
        for test_endpoint in test_endpoints:
            self.assertEqual(self.api._parse_endpoint(test_endpoint), ENDPOINT)

    @responses.activate
    def test_process_response(self):
        res = requests.Response()
        res.request = requests.Request(method="GET", url=f"{ENDPOINT}test").prepare()
        res.status_code = 401
        with self.assertRaises(AccessDeniedError):
            self.api._process_response(res)

        res.status_code = 404
        with self.assertRaises(APIError):
            self.api._process_response(res)

        res.status_code = 502
        with self.assertRaises(APIError):
            self.api._process_response(res)

        res.status_code = 200
        res._content = b'{"error": "test_error"}'
        with self.assertRaises(APIError):
            self.api._process_response(res)

        res._content = b'{invalid_json"'
        with self.assertRaises(APIError):
            self.api._process_response(res)

        res._content = b'{}'
        self.assertEqual(self.api._process_response(res), {})

        res._content = b'{"response": "ok"}'
        self.assertEqual(self.api._process_response(res), {"response": "ok"})

    @responses.activate
    def test_get(self):
        add(Response(GET, url=f"{ENDPOINT}test_get", json={"test_get": True}))

        self.assertEqual(self.api.get("test_get"), {"test_get": True})

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

        resp = self.api.post("test_post", {"test": True})

        self.assertIsInstance(resp, dict)
        self.assertEqual(resp, {"test_post": True})

    def test_is_authenticated(self):
        api = API(ENDPOINT)
        self.assertEqual(api.is_authenticated(), False)

    def test_url(self):
        self.assertEqual(self.api.url("test"), ENDPOINT + "test")