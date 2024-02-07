import json
import unittest

import aiohttp
import aresponses
from yarl import URL

from tesla_powerwall import API, AccessDeniedError, ApiError
from tesla_powerwall.const import User
from tests.unit import ENDPOINT, ENDPOINT_HOST, ENDPOINT_PATH


class TestAPI(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.aresponses = aresponses.ResponsesMockServer()
        await self.aresponses.__aenter__()

        self.session = aiohttp.ClientSession()
        self.api = API(ENDPOINT, http_session=self.session)

    async def asyncTearDown(self):
        await self.api.close()
        await self.session.close()
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
        self.assertEqual(self.api.url("test"), URL(ENDPOINT + "test"))

    async def test_login(self):
        jar = aiohttp.CookieJar(unsafe=True)
        async with aiohttp.ClientSession(cookie_jar=jar) as http_session:
            async with API(ENDPOINT, http_session=http_session) as api:
                username = User.CUSTOMER.value
                password = "password"
                email = "email@email.com"

                async def response_handler(request) -> aresponses.Response:
                    request_json = await request.json()

                    self.assertEqual(request_json["username"], username)
                    self.assertEqual(request_json["password"], password)
                    self.assertEqual(request_json["email"], email)

                    login_response = self.aresponses.Response(
                        text=json.dumps(
                            {
                                "email": request_json["email"],
                                "firstname": "Tesla",
                                "lastname": "Energy",
                                "roles": ["Home_Owner"],
                                "token": "x4jbH...XMP8w==",
                                "provider": "Basic",
                                "loginTime": "2023-03-25T13:10:48.9029581+01:00",
                            }
                        ),
                        headers={"Content-Type": "application/json"},
                    )
                    login_response.set_cookie("AuthCookie", "foo")
                    return login_response

                self.aresponses.add(
                    ENDPOINT_HOST,
                    f"{ENDPOINT_PATH}login/Basic",
                    "POST",
                    response_handler,
                )

                await api.login(username=username, email=email, password=password)

                self.aresponses.add(
                    ENDPOINT_HOST,
                    f"{ENDPOINT_PATH}logout",
                    "GET",
                    self.aresponses.Response(
                        text="", headers={"Content-Type": "application/json"}
                    ),
                )

                await api.logout()

                self.aresponses.assert_plan_strictly_followed()

    async def test_close(self):
        api_session = None
        async with API(ENDPOINT) as api:
            api_session = api._http_session
            self.assertFalse(api_session.closed)
        self.assertTrue(api_session.closed)

        async with aiohttp.ClientSession() as session:
            async with API(ENDPOINT, http_session=session) as api:
                api_session = api._http_session
                self.assertFalse(api_session.closed)

            self.assertFalse(api_session.closed)
        self.assertTrue(api_session.closed)

        api = API(ENDPOINT)
        api_session = api._http_session
        self.assertFalse(api_session.closed)
        await api.close()
        self.assertTrue(api_session.closed)

        async with aiohttp.ClientSession() as session:
            api_session = session
            api = API(ENDPOINT, http_session=session)
            self.assertFalse(api_session.closed)
            await api.close()
            self.assertFalse(api_session.closed)
        self.assertTrue(api_session.closed)
