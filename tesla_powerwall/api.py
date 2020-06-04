from json.decoder import JSONDecodeError
import requests
from urllib.parse import urljoin, urlparse, urlsplit, urlunparse, urlunsplit
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning

from .error import (
    AccessDeniedError,
    APIError,
    PowerwallUnreachableError,
)

class API(object):
    def __init__(self, 
        endpoint: str, 
        timeout: int = 10, 
        http_session: requests.Session = None,
        verify_ssl: bool = False,
        disable_insecure_warning: bool = True,
        dont_validate_response: bool = False):

        if disable_insecure_warning:
            disable_warnings(InsecureRequestWarning)

        self._endpoint = self._parse_endpoint(endpoint)
        self._timeout = timeout
        self._http_session = http_session if http_session else requests.Session()
        self._http_session.verify = verify_ssl
        self._dont_validate_response = dont_validate_response


    def _parse_endpoint(self, endpoint: str) -> str:
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

    def _process_response(self, response: str) -> dict:
        if response.status_code == 404:
            raise APIError("The url {} returned error 404".format(response.request.path_url))

        if response.status_code == 401 or response.status_code == 403:
            response_json = None
            try:
                response_json = response.json()
            except Exception:
                raise AccessDeniedError(response.request.path_url)
            else:
                raise AccessDeniedError(
                    response.request.path_url, response_json["error"]
                )

        if response.status_code == 502:
            raise PowerwallUnreachableError()

        try:
            response_json = response.json()
        except JSONDecodeError:
            raise APIError("Error while decoding json of response: {}".format(response.text))

        if response_json is None:
            return {}

        if "error" in response_json:
            raise APIError(response_json["error"])

        return response_json

    def get(
        self, path: str, needs_authentication: bool = False, headers: dict = {}
    ) -> dict:
        if needs_authentication and not self.is_authenticated():
            raise APIError("Authentication required to access {}".format(path))

        try:
            response = self._http_session.get(
                url=urljoin(self._endpoint, path),
                timeout=self._timeout,
                headers=headers,
            )
        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as e:
            raise PowerwallUnreachableError(e)

        return self._process_response(response)

    def post(
        self,
        path: str,
        payload: dict,
        needs_authentication: bool = False,
        headers: dict = {},
    ) -> dict:
        if needs_authentication and not self.is_authenticated():
            raise APIError("Authentication required to access {}".format(path))

        try:
            response = self._http_session.post(
                url=urljoin(self._endpoint, path),
                data=payload,
                timeout=self._timeout,
                headers=headers,
            )
        except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as e:
            raise PowerwallUnreachableError(e)

        return self._process_response(response)

    def is_authenticated(self) -> bool:
        return "AuthCookie" in self._http_session.cookies.keys()