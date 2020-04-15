import re
from datetime import datetime, timedelta

from .const import DEFAULT_KW_ROUND_PERSICION, MeterType
from .error import APIChangedError
from .helpers import convert_to_kw


class Response(object):
    """Basic Response object that can be constructed from a json response"""

    # A list of attributes that should be in the json_response
    _JSON_ATTRS = []
    # A list of attributes that may be in the json_response but aren"t required
    _OPTIONAL_JSON_ATTRS = []

    def __init__(self, json_response: dict, no_check: bool = False):
        self.json_response = json_response
        self._set_attrs(no_check)
        self.response_validated = not no_check

    def _set_attrs(self, no_check: bool = False) -> None:
        """Set attributes from _JSON_ATTRS as object properties. 
        Also checks wether the response is valid. 
        This can be disabled by passing no_check=True"""
        missing_attrs = []
        for attr in self.__class__._JSON_ATTRS:
            self._add_attr(attr, missing_attrs)

        if len(self.__class__._OPTIONAL_JSON_ATTRS) > 0:
            for attr in self.__class__._OPTIONAL_JSON_ATTRS:
                self._add_attr(attr)

        if not no_check:
            added_attrs = self._get_added_attrs()

        # We are missing some attributes in the json_response
        if not no_check and len(missing_attrs) > 0:
            raise APIChangedError(
                self.__class__, self.json_response, added_attrs, missing_attrs
            )

    def _add_attr(self, attr, missing_attrs=[]) -> None:
        # Make sure the attribute also exist in the json_response
        if attr in self.json_response:
            setattr(self, attr, self.json_response[attr])
        else:
            missing_attrs.append(attr)

    def _get_added_attrs(self) -> list:
        added_attrs = []
        for attr in self.json_response.keys():
            if attr not in self.__class__._JSON_ATTRS:
                added_attrs.append(attr)
        return added_attrs

    # Helper methods to make interaction with optional json attributes easier

    def has_optional_attrs(self) -> bool:
        return len(self.__class__._OPTIONAL_JSON_ATTRS) > 0

    def has_optional_attrs_set(self) -> bool:
        """Checks wether all optional attributes are present in the json response"""
        return set(
            self.__class__._OPTIONAL_JSON_ATTRS + self.__class__._JSON_ATTRS
        ) == set(self.json_response.keys())

    def get(self, key, default=None):
        """Equavivalent to dict.get"""
        return self.json_response.get(key, default)

    def has_key(self, key) -> bool:
        return key in self.json_response.keys()

    def __getitem__(self, key):
        return getattr(self, key)

    def __repr__(self) -> str:
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
        "region",
    ]

    _OPTIONAL_JSON_ATTRS = ["distributor", "utility", "retailer"]


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

    def __init__(self, json_response, no_check=False):
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

    _JSON_ATTRS = ["powerwalls", "has_sync", "sync", "states"]

    def __init__(self, json_response, no_check=False):
        super().__init__(json_response, no_check)
        self.status = PowerwallsStatusResponse(self.json_response, no_check=no_check)
        self.powerwalls = [
            ListPowerwallsResponse.PowerwallResponse(powerwall, no_check=no_check)
            for powerwall in self.powerwalls
        ]


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
