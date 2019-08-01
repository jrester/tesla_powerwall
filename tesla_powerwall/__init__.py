import requests
import logging

class ApiError(Exception):
    def __init__(self, error):
        super().__init__(f"Power Wall api error: {error}")

class PowerWallUnreachableError(Exception):
    def __init__(self):
        super().__init__(f"Site master or Power wall is unreachable!")


class MetersResponse:
    JSON_ATTRS = ["last_communication_time", "instant_power", "instant_reactive_power", "instant_apparent_power", "frequency", "energy_exported", "energy_imported", "instant_average_voltage", "instant_total_current", "i_a_current", "i_b_current", "i_c_current"]

    def __init__(self, response_json):
        self.response_json = response_json

        for attr in MetersResponse.JSON_ATTRS:
            setattr(self, attr, response_json[attr])

class PowerWall:
    def __init__(self, host):
        self.host = host

    def _get(self, endpoint, needs_authentication=False):
        logging.debug(f'Getting {self.host}/{endpoint}')
        response = requests.get(f'http://{self.host}/{endpoint}')

        if response.status_code == 502:
            raise PowerWallUnreachableError()


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
        return self.sitemaster["running"]

    @property
    def uptime(self):
        return self.sitemaster["uptime"]

    @property
    def connected_to_tesla(self):
        return self.sitemaster["connected_to_tesla"]

    @property
    def meters(self):
        return self._get("api/meters/aggregates")
    
    @property
    def solar(self):
        return MetersResponse(self.meters["solar"])

    @property
    def grid(self):
        return MetersResponse(self.meters["site"])

    @property
    def load(self):
        return MetersResponse(self.meters["load"])

    @property
    def battery(self):
        return MetersResponse(self.meters["battery"])

    @property
    def busway(self):
        return MetersResponse(self.meters["busway"])

    @property
    def frequency(self):
        return MetersResponse(self.meters["frequency"])

    @property
    def generator(self):
        return MetersResponse(self.meters["generator"])

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

    @property
    def home_power(self):
        return self.load.instant_power

    @property
    def grid_power(self):
        return self.grid.instant_power

    @property
    def solar_power(self):
        return self.solar.instant_power
    
    @property
    def battery_power(self):
        return self.battery.instant_power

    @property
    def sending_to_grid(self):
        return self.grid_power < 0

    @property
    def drawing_from_grid(self):
        return not self.sending_to_grid

    @property
    def sending_to_battery(self):
        return self.battery_power < 0

    @property
    def drawing_from_battery(self):
        return not self.sending_to_battery

    @property
    def sending_to_solar(self):
        return self.solar_power < 0

    @property
    def drawing_from_solar(self):
        return not self.sending_to_solar