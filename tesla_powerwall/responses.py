import re
from datetime import datetime, timedelta

from .const import (
    DEFAULT_KW_ROUND_PERSICION,
    DeviceType,
    MeterType,
    Roles,
)
from .helpers import assert_attribute, convert_to_kw


class Response:
    def __init__(self, response: dict):
        self.response = response

    def assert_attribute(self, attr: str):
        return assert_attribute(self.response, attr)

    def __repr__(self):
        return str(self.response)


class Meter(Response):
    """
    Attributes:
    - last_communication_time
    - instant_power
    - instant_reactive_power
    - instant_apparent_power
    - frequency
    - energy_exported
    - energy_imported
    - instant_average_voltage
    - instant_total_current
    - i_a_current
    - i_b_current
    - i_c_current
    - timeout
    """

    def __init__(self, meter: MeterType, response):
        self.meter = meter
        super().__init__(response)

    @property
    def instant_power(self):
        return self.assert_attribute("instant_power")

    @property
    def last_communication_time(self):
        return self.assert_attribute("last_communication_time")

    @property
    def frequency(self):
        return self.assert_attribute("frequency")

    @property
    def energy_exported(self):
        return self.assert_attribute("energy_exported")

    def get_energy_exported(self, precision=DEFAULT_KW_ROUND_PERSICION):
        return convert_to_kw(self.energy_exported, precision)

    @property
    def energy_imported(self):
        return self.assert_attribute("energy_imported")

    def get_energy_imported(self, precision=DEFAULT_KW_ROUND_PERSICION):
        return convert_to_kw(self.energy_imported, precision)

    @property
    def avarage_voltage(self):
        return self.assert_attribute("instant_average_voltage")

    def get_power(self, precision=DEFAULT_KW_ROUND_PERSICION):
        return convert_to_kw(self.instant_power, precision)

    def is_active(self, precision=DEFAULT_KW_ROUND_PERSICION) -> bool:
        return self.get_power(precision) != 0

    def is_drawing_from(self, precision=DEFAULT_KW_ROUND_PERSICION) -> bool:
        if self.meter == MeterType.LOAD:
            # Cannot draw from load
            return False
        else:
            return self.get_power(precision) > 0

    def is_sending_to(self, precision=DEFAULT_KW_ROUND_PERSICION):
        if self.meter == MeterType.LOAD:
            # For load the power is always positiv
            return self.get_power(precision) > 0
        else:
            return self.get_power(precision) < 0


class MetersAggregates(Response):
    def __init__(self, response):
        super().__init__(response)
        self.solar = Meter(
            MeterType.SOLAR, self.assert_attribute(MeterType.SOLAR.value)
        )
        self.site = Meter(MeterType.SITE, self.assert_attribute(MeterType.SITE.value))
        self.battery = Meter(
            MeterType.BATTERY, self.assert_attribute(MeterType.BATTERY.value)
        )
        self.load = Meter(MeterType.LOAD, self.assert_attribute(MeterType.LOAD.value))

    def get_meter(self, meter: MeterType) -> Meter:
        return getattr(self, meter.value)


class SiteMaster(Response):
    """
    Attributes:
    - running
    - connected_to_tesla
    - status
    - power_supply_mode
    """

    def __init__(self, response):
        super().__init__(response)

    @property
    def status(self):
        return self.assert_attribute("status")

    @property
    def is_running(self):
        return self.assert_attribute("running")

    @property
    def is_connected_to_tesla(self):
        return self.assert_attribute("connected_to_tesla")

    @property
    def is_power_supply_mode(self):
        return self.assert_attribute("power_supply_mode")


class SiteInfo(Response):
    """
    Attributes:
    - max_site_meter_power_kW
    - min_site_meter_power_kW
    - nominal_system_energy_kWh
    - nominal_system_power_kW
    - max_system_energy_kWh
    - max_system_power_kW
    - site_name
    - timezone
    - grid_code
    """

    def __init__(self, response):
        super().__init__(response)

    @property
    def nominal_system_energy(self):
        return self.assert_attribute("nominal_system_energy_kWh")

    @property
    def site_name(self):
        return self.assert_attribute("site_name")

    @property
    def timezone(self):
        return self.assert_attribute("timezone")


class PowerwallStatus(Response):
    """
    Attributes:
    * start_time
    * up_time_seconds
    * is_new
    * version
    * device_type
    * commission_count
    * sync_type
    * git_hash
    """

    _START_TIME_FORMAT = "%Y-%m-%d %H:%M:%S %z"
    _UP_TIME_SECONDS_REGEX = re.compile(
        r"((?P<hours>\d+?)h)?((?P<minutes>\d+?)m)?((?P<seconds>\d+?).)((?P<microseconds>\d+?)s)"
    )

    def _parse_uptime_seconds(self, up_time_seconds: str):
        match = PowerwallStatus._UP_TIME_SECONDS_REGEX.match(up_time_seconds)
        if not match:
            raise ValueError(
                "Unable to parse up time seconds {}".format(up_time_seconds)
            )

        time_params = {}
        for (name, param) in match.groupdict().items():
            if param:
                time_params[name] = int(param)

        return timedelta(**time_params)

    @property
    def up_time_seconds(self):
        up_time_seconds = assert_attribute(self.response, "up_time_seconds")
        return self._parse_uptime_seconds(up_time_seconds)

    @property
    def start_time(self):
        start_time = assert_attribute(self.response, "start_time")
        return datetime.strptime(start_time, self._START_TIME_FORMAT)

    @property
    def version(self):
        return self.assert_attribute("version")

    @property
    def device_type(self):
        return DeviceType(self.assert_attribute("device_type"))


class LoginResponse(Response):
    """
    Attributes
    - email
    - firstname
    - lastname
    - roles
    - token
    - provider
    - loginTime
    """

    @property
    def firstname(self):
        return self.assert_attribute("firstname")

    @property
    def lastname(self):
        return self.assert_attribute("lastname")

    @property
    def token(self):
        return self.assert_attribute("token")

    @property
    def roles(self):
        return [Roles(role) for role in self.assert_attribute("roles")]

    @property
    def login_time(self):
        return self.assert_attribute("login_time")


class Solar(Response):
    """
    Attributes
    - brand
    - model
    - power_rating_watts
    """

    @property
    def brand(self):
        return self.assert_attribute("brand")

    @property
    def model(self):
        return self.assert_attribute("model")

    @property
    def power_rating_watts(self):
        return self.assert_attribute("power_rating_watts")
