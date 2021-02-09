from json.decoder import JSONDecodeError
from typing import List
from urllib.parse import urljoin

import requests
from packaging.version import Version
from requests.api import request
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning
from http.client import responses

from .error import AccessDeniedError, APIError, PowerwallUnreachableError


class API(object):
    def __init__(
        self,
        endpoint: str,
        timeout: int = 10,
        http_session: requests.Session = None,
        verify_ssl: bool = False,
        disable_insecure_warning: bool = True,
    ) -> None:

        if disable_insecure_warning:
            disable_warnings(InsecureRequestWarning)

        self._endpoint = self._parse_endpoint(endpoint)
        self._timeout = timeout
        self._http_session = http_session if http_session else requests.Session()
        self._http_session.verify = verify_ssl

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
    def _handle_error(response: requests.Response) -> None:
        if response.status_code == 404:
            raise APIError(
                "The url {} returned error 404".format(response.request.path_url)
            )

        if response.status_code == 401 or response.status_code == 403:
            response_json = None
            try:
                response_json = response.json()
            except Exception:
                raise AccessDeniedError(response.request.path_url)
            else:
                raise AccessDeniedError(
                    response.request.path_url,
                    response_json.get("error"),
                    response_json.get("message"),
                )

        if response.text is not None and len(response.text) > 0:
            raise APIError(
                "API returned status code '{}: {}' with body: {}".format(
                    response.status_code,
                    responses.get(response.status_code),
                    response.text,
                )
            )
        else:
            raise APIError(
                "API returned status code '{}: {}' ".format(
                    response.status_code, responses.get(response.status_code)
                )
            )

    def _process_response(self, response: requests.Response) -> dict:
        if response.status_code >= 400:
            # API returned some sort of error that must be handled
            self._handle_error(response)

        try:
            response_json = response.json()
        except JSONDecodeError:
            raise APIError(
                "Error while decoding json of response: {}".format(response.text)
            )

        if response_json is None:
            return {}

        # Newer versions of the powerwall do not return such values anymore
        # Kept for backwards compability or if the API changes again
        if "error" in response_json:
            raise APIError(response_json["error"])

        return response_json

    def url(self, path: str):
        return urljoin(self._endpoint, path)

    def get(self, path: str, headers: dict = {}) -> dict:
        try:
            response = self._http_session.get(
                url=self.url(path),
                timeout=self._timeout,
                headers=headers,
            )
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.ReadTimeout,
        ) as e:
            raise PowerwallUnreachableError(e)

        return self._process_response(response)

    def post(
        self,
        path: str,
        payload: dict,
        headers: dict = {},
    ) -> dict:
        try:
            response = self._http_session.post(
                url=self.url(path),
                data=payload,
                timeout=self._timeout,
                headers=headers,
            )
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.ReadTimeout,
        ) as e:
            raise PowerwallUnreachableError(e)

        return self._process_response(response)

    def is_authenticated(self) -> bool:
        return "AuthCookie" in self._http_session.cookies.keys()

    def login(
        self, username: str, email: str, password: str, force_sm_off: bool = False
    ) -> dict:

        # force_sm_off is referred to as 'shouldForceLogin' in the web source code
        return self.post(
            "login/Basic",
            {
                "username": username,
                "email": email,
                "password": password,
                "force_sm_off": force_sm_off,
            },
        )

    def logout(self):
        if not self.is_authenticated():
            raise APIError("Must be logged in to log out")
        # The api unsets the auth cookie and the token is invalidated
        self.get("logout")

    # Endpoints are mapped to one method by <verb>_<path> so they can be easily accessed

    def get_system_status_soe(self) -> dict:
        return self.get("system_status/soe")

    def get_meters_aggregates(self) -> dict:
        return self.get("meters/aggregates")

    def get_sitemater_run(self):
        return self.get("sitemaster/run")

    def get_sitemaster_stop(self):
        return self.get("sitemaster/stop")

    def get_sitemaster(self) -> dict:
        return self.get("sitemaster")

    def get_status(self) -> dict:
        return self.get("status")

    # Endpoint not available in 1.46 and up
    def get_device_type(self):
        return self.get("device_type")

    def get_customer_registration(self):
        return self.get("customer/registration")

    def get_powerwalls(self):
        return self.get("powerwalls")

    def get_operation(self):
        return self.get("operation")

    def get_networks(self) -> list:
        return self.get("networks")

    def get_phase_usage(self):
        return self.get("powerwalls/phase_usages")

    def post_sitemaster_run_for_commissioning(self):
        return self.post("sitemaster/run_for_commissioning", payload={})

    def get_solars(self):
        return self.get("solars")

    def get_config(self):
        return self.get("config")

    def get_logs(self):
        return self.get("getlogs")

    def get_meters(self) -> list:
        return self.get("meters")

    def get_installer(self) -> dict:
        return self.get("installer")

    def get_solar_brands(self) -> List[str]:
        return self.get("solars/brands")

    def get_system_update_status(self) -> dict:
        return self.get("system/update/status")

    def get_system_status_grid_status(self) -> dict:
        return self.get("system_status/grid_status")

    def get_site_info(self) -> dict:
        return self.get("site_info")

    def get_site_info_grid_codes(self) -> list:
        return self.get("site_info/grid_codes")

    def post_site_info_site_name(self, body: dict) -> dict:
        return self.post("site_info/site_name", body)
