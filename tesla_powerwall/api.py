import aiohttp
from http.client import responses
from json.decoder import JSONDecodeError
from types import TracebackType
from typing import Any, List, Optional, Type
from urllib.parse import urljoin

from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning

from .error import AccessDeniedError, ApiError, PowerwallUnreachableError


class API(object):
    def __init__(
        self,
        endpoint: str,
        timeout: int = 10,
        http_session: Optional[aiohttp.ClientSession] = None,
        verify_ssl: bool = False,
        disable_insecure_warning: bool = True,
    ) -> None:
        if disable_insecure_warning:
            disable_warnings(InsecureRequestWarning)

        self._endpoint = self._parse_endpoint(endpoint)
        self._timeout = aiohttp.ClientTimeout(total=timeout)
        self._owns_http_session = False if http_session else True
        self._ssl = None if verify_ssl else False

        if http_session:
            self._owns_http_session = False
            self._http_session = http_session
        else:
            self._owns_http_session = True

            # Allow unsafe cookies so that folks can use IP addresses in their configs
            # See: https://docs.aiohttp.org/en/v3.7.3/client_advanced.html#cookie-safety
            jar = aiohttp.CookieJar(unsafe=True)
            self._http_session = aiohttp.ClientSession(cookie_jar=jar)

    @staticmethod
    def _parse_endpoint(endpoint: str) -> str:
        if endpoint.startswith("https"):
            endpoint = endpoint
        elif endpoint.startswith("http"):
            endpoint = endpoint.replace("http", "https")
        else:
            # Use str.format instead of f'strings to be backwards compatible
            endpoint = "https://{}".format(endpoint)

        if not endpoint.endswith("api") and not endpoint.endswith("/"):
            endpoint += "/api/"
        elif endpoint.endswith("api"):
            endpoint += "/"
        elif endpoint.endswith("/") and not endpoint.endswith("api/"):
            endpoint += "api/"

        return endpoint

    @staticmethod
    async def _handle_error(response: aiohttp.ClientResponse) -> None:
        if response.status == 404:
            raise ApiError(
                "The url {} returned error 404".format(str(response.real_url))
            )

        if response.status == 401 or response.status == 403:
            response_json = None
            try:
                response_json = await response.json()
            except Exception:
                raise AccessDeniedError(str(response.real_url))
            else:
                raise AccessDeniedError(
                    str(response.real_url),
                    response_json.get("error"),
                    response_json.get("message"),
                )

        response_text = await response.text()
        if response_text is not None and len(response_text) > 0:
            raise ApiError(
                "API returned status code '{}: {}' with body: {}".format(
                    response.status,
                    responses.get(response.status),
                    response_text,
                )
            )
        else:
            raise ApiError(
                "API returned status code '{}: {}' ".format(
                    response.status, responses.get(response.status)
                )
            )

    async def _process_response(self, response: aiohttp.ClientResponse) -> dict:
        if response.status >= 400:
            # API returned some sort of error that must be handled
            await self._handle_error(response)

        content = await response.read()
        if len(content) == 0:
            return {}

        try:
            response_json = await response.json(content_type=None)
        except JSONDecodeError:
            raise ApiError(
                "Error while decoding json of response: {}".format(response.text)
            )

        if response_json is None:
            return {}

        # Newer versions of the powerwall do not return such values anymore
        # Kept for backwards compability or if the API changes again
        if "error" in response_json:
            raise ApiError(response_json["error"])

        return response_json

    def url(self, path: str):
        return urljoin(self._endpoint, path)

    async def get(self, path: str, headers: dict = {}) -> Any:
        try:
            response = await self._http_session.get(
                url=self.url(path),
                timeout=self._timeout,
                headers=headers,
                ssl=self._ssl,
            )
        except aiohttp.ClientConnectionError as e:
            raise PowerwallUnreachableError(str(e))

        return await self._process_response(response)

    async def post(
        self,
        path: str,
        payload: dict,
        headers: dict = {},
    ) -> Any:
        try:
            response = await self._http_session.post(
                url=self.url(path),
                json=payload,
                timeout=self._timeout,
                headers=headers,
                ssl=self._ssl,
            )
        except aiohttp.ClientConnectionError as e:
            raise PowerwallUnreachableError(str(e))

        return await self._process_response(response)

    def is_authenticated(self) -> bool:
        for cookie in self._http_session.cookie_jar:
            if "AuthCookie" == cookie.key:
                return True
        return False

    async def login(
        self,
        username: str,
        email: str,
        password: str,
        force_sm_off: bool = False,
    ) -> dict:
        # force_sm_off is referred to as 'shouldForceLogin' in the web source code
        return await self.post(
            "login/Basic",
            {
                "username": username,
                "email": email,
                "password": password,
                "force_sm_off": force_sm_off,
            },
        )

    async def logout(self) -> None:
        if not self.is_authenticated():
            raise ApiError("Must be logged in to log out")
        # The api unsets the auth cookie and the token is invalidated
        await self.get("logout")

    async def close(self) -> None:
        if self._owns_http_session:
            await self._http_session.close()

    async def __aenter__(self) -> "API":
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        await self.close()

    # Endpoints are mapped to one method by <verb>_<path> so they can be easily accessed

    async def get_system_status(self) -> dict:
        return await self.get("system_status")

    async def get_system_status_soe(self) -> dict:
        return await self.get("system_status/soe")

    async def get_meters_aggregates(self) -> dict:
        return await self.get("meters/aggregates")

    async def get_sitemaster_run(self):
        return await self.get("sitemaster/run")

    async def get_sitemaster_stop(self):
        return await self.get("sitemaster/stop")

    async def get_sitemaster(self) -> dict:
        return await self.get("sitemaster")

    async def get_status(self) -> dict:
        return await self.get("status")

    async def get_customer_registration(self) -> dict:
        return await self.get("customer/registration")

    async def get_powerwalls(self):
        return await self.get("powerwalls")

    async def get_operation(self) -> dict:
        return await self.get("operation")

    async def get_networks(self) -> list:
        return await self.get("networks")

    async def get_phase_usage(self):
        return await self.get("powerwalls/phase_usages")

    async def post_sitemaster_run_for_commissioning(self):
        return await self.post("sitemaster/run_for_commissioning", payload={})

    async def get_solars(self):
        return await self.get("solars")

    async def get_config(self):
        return await self.get("config")

    async def get_logs(self):
        return await self.get("getlogs")

    async def get_meters(self) -> list:
        return await self.get("meters")

    async def get_meters_site(self) -> list:
        return await self.get("meters/site")

    async def get_meters_solar(self) -> list:
        return await self.get("meters/solar")

    async def get_installer(self) -> dict:
        return await self.get("installer")

    async def get_solar_brands(self) -> List[str]:
        return await self.get("solars/brands")

    async def get_system_update_status(self) -> dict:
        return await self.get("system/update/status")

    async def get_system_status_grid_status(self) -> dict:
        return await self.get("system_status/grid_status")

    async def get_site_info(self) -> dict:
        return await self.get("site_info")

    async def get_site_info_grid_codes(self) -> list:
        return await self.get("site_info/grid_codes")

    async def post_site_info_site_name(self, body: dict) -> dict:
        return await self.post("site_info/site_name", body)

    async def post_islanding_mode(self, body: dict) -> dict:
        return await self.post("v2/islanding/mode", body)
