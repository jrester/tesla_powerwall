import re
from datetime import datetime, timedelta

from .const import (DEFAULT_KW_ROUND_PERSICION, DeviceType, MeterType,
                    SyncType, UpdateState)
from .error import APIChangedError
from .helpers import convert_to_kw


# Looks for attribute in responses and throws APIChangedError if it was not found
def assert_attribute(response: dict, attribute: str, endpoint: str=''):
        value = response.get(attribute)
        if value is None:
            if len(endpoint) > 0:
                raise APIChangedError(attribute, response, endpoint)
            else:
                raise APIChangedError(attribute, response, endpoint)
        return value

class Response(object):
    ENDPOINT = ''

    def __init__(self, response: dict):
        self.response = response

    def assert_attribute(self, attribute: str):
        assert_attribute(self.response, attribute, self.ENDPOINT)

    def __getattr__(self, attribute):
        return self.assert_attribute(attribute)


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

    def __init__(self, json_response: dict, meter: MeterType = None, no_check=False):
        super().__init__(json_response, no_check=no_check)
        self.meter = meter

    def is_sending_to(self, precision=DEFAULT_KW_ROUND_PERSICION):
        if self.meter == MeterType.LOAD:
            return convert_to_kw(self.instant_power, precision) > 0
        else:
            return convert_to_kw(self.instant_power, precision) < 0

    def is_drawing_from(self, precision=DEFAULT_KW_ROUND_PERSICION):
        if self.meter == MeterType.LOAD:
            # Cannot draw from load
            return False
        else:
            return convert_to_kw(self.instant_power, precision) > 0

    def is_active(self, precision=DEFAULT_KW_ROUND_PERSICION):
        return convert_to_kw(self.instant_power, precision) != 0

    def get_power(self, precision=DEFAULT_KW_ROUND_PERSICION):
        """Returns power sent/drawn in kWh"""
        return convert_to_kw(self.instant_power, precision)


class MetersAggregateResponse(Response):
    """
    Response for "meters/aggregates"
    """

    def __init__(self, json_response, no_check=False):
        self.json_response = json_response
        for meter in MeterType:
            if meter.value in json_response:
                setattr(
                    self,
                    meter.value,
                    MetersResponse(json_response[meter.value], meter, no_check),
                )

    def get(self, meter: MeterType) -> MetersResponse:
        return getattr(self, meter.value)


class MeterDetailsResponse(Response):
    _JSON_ATTRS = ["id", "location", "type", "cts", "inverted", "connection"]

    def __init__(self, json_response, no_check=False):
        super().__init__(json_response, no_check)
        self.cached_readings = MetersResponse(
            json_response["Cached_readings"], no_check=no_check
        )


class SitemasterResponse(Response):
    """
    Attributes:
    * running
    * connectd_to_tesla
    * status
    """
    ENDPOINT = 'sitemaster'
     
    def is_running(self):
        return self.assert_attribute('running')

    def is_connected_to_tesla(self):
        return self.assert_attribute('connected_to_tesla')


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
    ]

    _OPTIONAL_JSON_ATTRS = ["distributor", "utility", "retailer", "region"]


class CustomerRegistrationResponse(Response):
    _JSON_ATTRS = [
        "privacy_notice",
        "limited_warranty",
        "grid_services",
        "marketing",
        "registered",
        "timed_out_registration",
    ]

class PowerwallStatus(Response):
    _START_TIME_FORMAT = "%Y-%m-%d %H:%M:%S %z"
    _UP_TIME_SECONDS_REGEX = re.compile(
        r"((?P<hours>\d+?)h)((?P<minutes>\d+?)m)((?P<seconds>\d+?).)((?P<microseconds>\d+?)s)"
    )

    def _parse_uptime_seconds(self, up_time_seconds: str):
        match = PowerwallStatusResponse._UP_TIME_SECONDS_REGEX.match(up_time_seconds)
        if not match:
            raise ValueError("Unable to parse up time seconds {}".format(up_time_seconds))

        time_params = {}
        for (name, param) in match.groupdict().items():
            if param:
                time_params[name] = int(param)

        return timedelta(**time_params)

    def get_up_time_seconds(self):
        return self._parse_uptime_seconds(self.up_time_seconds)

    def get_start_time(self):
        return datetime.strptime(self.start_time, self._START_TIME_FORMAT)


        


class PowerwallStatusResponse(Response):
    _JSON_ATTRS = [
        "start_time",
        "up_time_seconds",
        "is_new",
        "version",
        "git_hash",
    ]
    _OPTIONAL_JSON_ATTRS = [
        ("device_type", DeviceType),
        "commission_count",
        "sync_type"
    ]


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
    class PowerwallResponse(Response):
        _JSON_ATTRS = [
            "PackagePartNumber",
            "PackageSerialNumber",
            "type",
            "grid_state",
            "grid_reconnection_time_seconds",
            "under_phase_detection",
            "updating",
            "commissioning_diagnostic",
            "update_diagnostic",
        ]

        _OPTIONAL_JSON_ATTRS = ["Type", "bc_type"]

    _JSON_ATTRS = ["powerwalls", "has_sync", "sync", "states"]

    def __init__(self, json_response, no_check=False):
        super().__init__(json_response, no_check)
        self.status = PowerwallsStatusResponse(self.json_response, no_check=no_check)
        self.powerwalls = [
            ListPowerwallsResponse.PowerwallResponse(powerwall, no_check=no_check)
            for powerwall in self.powerwalls
        ]


class SolarsResponse(Response):
    # _JSON_ATTRS = ["brand", "model", "power_rating_watts"]
    def get_brand(self):
        return self.brand

    def get_model(self):
        return self.model

    def get_power_raing_watts(self):
        return self.power_rating_watts


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


class UpdateStatusResponse(Response):
    _JSON_ATTRS = [
        ("state", UpdateState),
        "info",
        "current_time",
        "last_status_time",
        "version",
        "offline_updating",
        "offline_update_error",
        "estimated_bytes_per_second",
    ]

    def __init__(self, json_response, no_check=False):
        super().__init__(json_response, no_check=no_check)