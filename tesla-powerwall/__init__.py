import requests
import logging

class ApiError(Exception):
    def __init__(self, error):
        super().__init__(f"Power Wall api error: {error}")

class PowerWallOffError(Exception):
    def __init__(self):
        super().__init__(f"Site master or Power wall is off!")

class PowerWall:
    def __init__(self, api_url):
        self.api_url = api_url

    def _get(self, endpoint, needs_authentication=False):
        logging.debug(f'Getting {self.api_url}/{endpoint}')
        response = requests.get(f'{self.api_url}/{endpoint}')

        if response.status_code == 502:
            raise PowerWallOffError()


        response_json = response.json()

        if 'error' in response_json:
            raise ApiError(response_json['error'])

        return response_json

    @property
    def charge(self):
        return self._get('api/system_status/soe')['percentage']

    @property
    def sitemaster(self):
        return self._get("api/sitemaster")

    @property
    def running(self):
        return self.sitemaster()["running"]

    @property
    def uptime(self):
        return self.sitemaster()["uptime"]

    @property
    def connected_to_tesla(self):
        return self.sitemaster()["connected_to_tesla"]

    @property
    def meters(self):
        return self._get("api/meters/aggregates")
    
    @property
    def solar(self):
        return self.meters()["solar"]

    @property
    def site(self):
        return self.meters()["meters"]

    @property
    def load(self):
        return self.meters()["load"]

    @property
    def battery(self):
        return self.meters()["battery"]

    @property
    def busway(self):
        return self.meters()["busway"]

    @property
    def frequency(self):
        return self.meters()["frequency"]

    @property
    def generator(self):
        return self.meters()["generator"]


    @property
    def solar_detailed(self):
        return self._get("api/meters/solar")

    @property
    def grid_status(self):
        return self._get("api/system_status/grid_status")["grid_status"]

    @property
    def site_info(self):
        return self._get("api/site_info")

    @property
    def status(self):
        return self._get("api/site_info/status")