from datetime import datetime, timedelta
import re

from .const import MeterType
from .helpers import convert_to_kwh


class Response(object):
    """Basic Response object that can be constructed from a json response"""

    def __init__(self, json_response: dict):
        self.json_response = json_response
        self._set_attrs()

    def _set_attrs(self):
        for attr in self.__class__._JSON_ATTRS:
            self._add_attr(attr)

    def _add_attr(self, attr: str):
        if attr in self.json_response:
            setattr(self, attr, self.json_response[attr])
        else:
            raise ValueError(
                f"Missing key '{attr}' in response from Powerwall. Either the Powerwall sent an invalid response or the API changed!"
            )

    def __repr__(self):
        return str(self.json_response)


class MetersResponse(Response):
    """Response for a single Meter
    Usually a nested item in the MetersAggregateResponse
    """

    _JSON_ATTRS = [
        "last_communication_time",
        "instant_power",  # The power that is supplied/drawn from the meter
        "instant_reactive_power",
        "instant_apparent_power",
        "frequency",
        "energy_exported",
        "energy_imported",
        "instant_average_voltage",
        "instant_total_current",
        "i_a_current",
        "i_b_current",
        "i_c_current",
        "timeout",
    ]

    def __init__(self, json_response: dict, meter: MeterType = None):
        super().__init__(json_response)
        self.meter = meter

    def is_sending_to(self, rounded=True):
        if self.meter == MeterType.LOAD:
            return convert_to_kwh(self.instant_power, rounded) > 0
        else:
            return convert_to_kwh(self.instant_power, rounded) < 0

    def is_drawing_from(self, rounded=True):
        if self.meter == MeterType.LOAD:
            # Cannot draw from load
            return False
        else:
            return convert_to_kwh(self.instant_power, rounded) > 0

    def is_active(self, rounded=True):
        return convert_to_kwh(self.instant_power, rounded) != 0

    def get_power(self, rounded=True):
        """Returns power sent/drawn in kWh"""
        return convert_to_kwh(self.instant_power, rounded)


class MetersAggregateResponse(Response):
    """
    Response for "meters/aggregates"
    """

    def __init__(self, json_response):
        self.json_response = json_response
        for meter in MeterType:
            if meter.value in json_response:
                setattr(
                    self, meter.value, MetersResponse(json_response[meter.value], meter)
                )

    def get(self, meter: MeterType) -> MetersResponse:
        return getattr(self, meter.value)


class MeterDetailsResponse(Response):
    _JSON_ATTRS = ["id", "location", "type", "cts", "inverted", "connection"]

    def __init__(self, json_response):
        super().__init__(json_response)
        self.cached_readings = MetersResponse(json_response["Cached_readings"])


class SitemasterResponse(Response):
    _JSON_ATTRS = ["status", "running", "connected_to_tesla"]


class SiteInfoResponse(Response):
    _JSON_ATTRS = [
        "max_site_meter_power_kW",
        "min_site_meter_power_kW",
        "nominal_system_energy_kWh",
        "nominal_system_power_kW",
        "max_system_energy_kWh",
        "max_system_power_kW",
        "site_name",
        "timezone",
        "grid_code",
        "grid_voltage_setting",
        "grid_freq_setting",
        "grid_phase_setting",
        "country",
        "state",
        "distributor",
        "utility",
        "retailer",
        "region",
    ]


class CustomerRegistrationResponse(Response):
    _JSON_ATTRS = [
        "privacy_notice",
        "limited_warranty",
        "grid_services",
        "marketing",
        "registered",
        "timed_out_registration",
    ]


class PowerwallStatusResponse(Response):
    _START_TIME_FORMAT = "%Y-%m-%d %H:%M:%S %z"
    _UP_TIME_SECONDS_REGEX = re.compile(
        r"((?P<hours>\d+?)h)((?P<minutes>\d+?)m)((?P<seconds>\d+?).)((?P<microseconds>\d+?)s)"
    )

    _JSON_ATTRS = ["start_time", "up_time_seconds", "is_new", "version", "git_hash"]

    def __init__(self, json_response):
        self.json_response = json_response

        resp = json_response
        resp["start_time"] = datetime.strptime(
            json_response["start_time"], PowerwallStatusResponse._START_TIME_FORMAT
        )
        resp["up_time_seconds"] = self._parse_uptime_seconds(
            json_response["up_time_seconds"]
        )

        self._set_attrs()

    def _parse_uptime_seconds(self, up_time_seconds: str):
        match = self.__class__._UP_TIME_SECONDS_REGEX.match(up_time_seconds)
        if not match:
            raise ValueError(f"Unable to parse up time seconds {up_time_seconds}")

        time_params = {}
        for (name, param) in match.groupdict().items():
            if param:
                time_params[name] = int(param)

        return timedelta(**time_params)


class PowerwallsStatusResponse(Response):
    _JSON_ATTRS = [
        "enumerating",
        "updating",
        "checking_if_offgrid",
        "running_phase_detection",
        "phase_detection_last_error",
        "bubble_shedding",
        "on_grid_check_error",
        "grid_qualifying",
        "grid_code_validating",
        "phase_detection_not_available",
    ]


class ListPowerwallsResponse(Response):
    _JSON_ATTRS = ["powerwalls", "has_sync", "sync", "states"]

    def __init__(self, json_response):
        super().__init__(json_response)
        self.status = PowerwallsStatusResponse(self.json_response)


class SolarsResponse(Response):
    _JSON_ATTRS = ["brand", "model", "power_rating_watts"]


class LoginResponse(Response):
    _JSON_ATTRS = [
        "email",
        "firstname",
        "lastname",
        "roles",
        "token",
        "provider",
        "loginTime",
    ]
