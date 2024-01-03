import unittest

import aiohttp
import aresponses

from tesla_powerwall import API, AccessDeniedError, ApiError, PowerwallUnreachableError
from tests.unit import (
    ENDPOINT_HOST,
    ENDPOINT_PATH,
    ENDPOINT,
)


class TestAPI(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.aresponses = aresponses.ResponsesMockServer()
        await self.aresponses.__aenter__()

        self.session = aiohttp.ClientSession()
        self.api = API(ENDPOINT, http_session=self.session)

    async def asyncTearDown(self):
        await self.api.close()
        await self.aresponses.__aexit__(None, None, None)

    def test_parse_endpoint(self):
        test_endpoints = [
            "1.1.1.1",
            "http://1.1.1.1",
            "https://1.1.1.1/api/",
            "https://1.1.1.1/api",
            "https://1.1.1.1/",
        ]
        for test_endpoint in test_endpoints:
            self.assertEqual(self.api._parse_endpoint(test_endpoint), ENDPOINT)

    async def test_process_response(self):
        status = 0
        text = None

        def response_handler(request):
            return self.aresponses.Response(status=status, text=text)

        self.aresponses.add(
            ENDPOINT_HOST,
            f"{ENDPOINT_PATH}test",
            "GET",
            response_handler,
            repeat=self.aresponses.INFINITY,
        )

        status = 401
        async with self.session.get(f"{ENDPOINT}test") as response:
            with self.assertRaises(AccessDeniedError):
                await self.api._process_response(response)

        status = 404
        async with self.session.get(f"{ENDPOINT}test") as response:
            with self.assertRaises(ApiError):
                await self.api._process_response(response)

        status = 502
        async with self.session.get(f"{ENDPOINT}test") as response:
            with self.assertRaises(ApiError):
                await self.api._process_response(response)

        status = 200
        text = '{"error": "test_error"}'
        async with self.session.get(f"{ENDPOINT}test") as response:
            with self.assertRaises(ApiError):
                await self.api._process_response(response)

        status = 200
        text = '{invalid_json"'
        async with self.session.get(f"{ENDPOINT}test") as response:
            with self.assertRaises(ApiError):
                await self.api._process_response(response)

        status = 200
        text = "{}"
        async with self.session.get(f"{ENDPOINT}test") as response:
            self.assertEqual(await self.api._process_response(response), {})

        status = 200
        text = '{"response": "ok"}'
        async with self.session.get(f"{ENDPOINT}test") as response:
            self.assertEqual(
                await self.api._process_response(response), {"response": "ok"}
            )

    async def test_get(self):
        self.aresponses.add(
            ENDPOINT_HOST,
            f"{ENDPOINT_PATH}test_get",
            "GET",
            self.aresponses.Response(text='{"test_get": true}'),
        )

        self.assertEqual(await self.api.get("test_get"), {"test_get": True})

        self.aresponses.assert_plan_strictly_followed()

    async def test_post(self):
        self.aresponses.add(
            ENDPOINT_HOST,
            f"{ENDPOINT_PATH}test_post",
            "POST",
            self.aresponses.Response(
                text='{"test_post": true}', headers={"Content-Type": "application/json"}
            ),
        )

        resp = await self.api.post("test_post", {"test": True})
        self.assertIsInstance(resp, dict)
        self.assertEqual(resp, {"test_post": True})

        self.aresponses.assert_plan_strictly_followed()

    async def test_is_authenticated(self):
        self.assertEqual(self.api.is_authenticated(), False)

        self.session.cookie_jar.update_cookies(cookies={"AuthCookie": "foo"})
        self.assertEqual(self.api.is_authenticated(), True)

    def test_url(self):
        self.assertEqual(self.api.url("test"), ENDPOINT + "test")

    async def test_logout(self):
        self.aresponses.add(
            ENDPOINT_HOST,
            f"{ENDPOINT_PATH}logout",
            "GET",
            self.aresponses.Response(
                text="", headers={"Content-Type": "application/json"}
            ),
        )

        self.session.cookie_jar.update_cookies(cookies={"AuthCookie": "foo"})
        await self.api.logout()

        self.aresponses.assert_plan_strictly_followed()
