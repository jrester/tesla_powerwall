import re
from datetime import datetime, timedelta
from typing import List

from .const import DEFAULT_KW_ROUND_PERSICION, DeviceType, MeterType, Roles
from .error import MeterNotAvailableError
from .helpers import assert_attribute, convert_to_kw


class Response:
    def __init__(self, response: dict) -> None:
        self.response = response

    def assert_attribute(self, attr: str) -> any:
        return assert_attribute(self.response, attr)

    def __repr__(self) -> str:
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

    def __init__(self, meter: MeterType, response) -> None:
        self.meter = meter
        super().__init__(response)

    @property
    def instant_power(self) -> float:
        return self.assert_attribute("instant_power")

    @property
    def last_communication_time(self) -> str:
        return self.assert_attribute("last_communication_time")

    @property
    def frequency(self) -> float:
        return self.assert_attribute("frequency")

    @property
    def energy_exported(self) -> float:
        return self.assert_attribute("energy_exported")

    def get_energy_exported(self, precision=DEFAULT_KW_ROUND_PERSICION) -> float:
        return convert_to_kw(self.energy_exported, precision)

    @property
    def energy_imported(self) -> float:
        return self.assert_attribute("energy_imported")

    def get_energy_imported(self, precision=DEFAULT_KW_ROUND_PERSICION) -> float:
        return convert_to_kw(self.energy_imported, precision)

    @property
    def instant_total_current(self) -> float:
        return self.assert_attribute("instant_total_current")

    def get_instant_total_current(self, precision=DEFAULT_KW_ROUND_PERSICION) -> float:
        return round(self.instant_total_current, precision)

    @property
    def average_voltage(self) -> float:
        return self.assert_attribute("instant_average_voltage")

    def get_power(self, precision=DEFAULT_KW_ROUND_PERSICION) -> float:
        return convert_to_kw(self.instant_power, precision)

    def is_active(self, precision=DEFAULT_KW_ROUND_PERSICION) -> bool:
        return self.get_power(precision) != 0

    def is_drawing_from(self, precision=DEFAULT_KW_ROUND_PERSICION) -> bool:
        if self.meter == MeterType.LOAD:
            # Cannot draw from load
            return False
        else:
            return self.get_power(precision) > 0

    def is_sending_to(self, precision=DEFAULT_KW_ROUND_PERSICION) -> bool:
        if self.meter == MeterType.LOAD:
            # For load the power is always positiv
            return self.get_power(precision) > 0
        else:
            return self.get_power(precision) < 0


class MetersAggregates(Response):
    def __init__(self, response) -> str:
        super().__init__(response)
        self.meters = [MeterType(key) for key in response.keys()]

    def __getattribute__(self, attr) -> any:
        if attr.upper() in MeterType.__dict__:
            m = MeterType(attr)
            if m in self.meters:
                return self.get_meter(m)
            else:
                raise MeterNotAvailableError(m, self.meters)
        else:
            return object.__getattribute__(self, attr)

    def get_meter(self, meter: MeterType) -> Meter:
        if meter in self.meters:
            return Meter(meter, self.assert_attribute(meter.value))
        else:
            return None


class SiteMaster(Response):
    """
    Attributes:
    - running
    - connected_to_tesla
    - status
    - power_supply_mode
    """

    def __init__(self, response) -> None:
        super().__init__(response)

    @property
    def status(self) -> str:
        return self.assert_attribute("status")

    @property
    def is_running(self) -> bool:
        return self.assert_attribute("running")

    @property
    def is_connected_to_tesla(self) -> bool:
        return self.assert_attribute("connected_to_tesla")

    @property
    def is_power_supply_mode(self) -> bool:
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

    def __init__(self, response) -> None:
        super().__init__(response)

    @property
    def nominal_system_energy(self) -> int:
        return self.assert_attribute("nominal_system_energy_kWh")

    @property
    def site_name(self) -> str:
        return self.assert_attribute("site_name")

    @property
    def timezone(self) -> str:
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
        r"^((?P<days>[\.\d]+?)d)?((?P<hours>[\.\d]+?)h)?((?P<minutes>[\.\d]+?)m)?((?P<seconds>[\.\d]+?)s)?$"
    )

    def _parse_uptime_seconds(self, up_time_seconds: str) -> timedelta:
        match = PowerwallStatus._UP_TIME_SECONDS_REGEX.match(up_time_seconds)
        if not match:
            raise ValueError(
                "Unable to parse up time seconds {}".format(up_time_seconds)
            )

        time_params = {}
        for (name, param) in match.groupdict().items():
            if param:
                time_params[name] = float(param)

        return timedelta(**time_params)

    @property
    def up_time_seconds(self) -> timedelta:
        up_time_seconds = assert_attribute(self.response, "up_time_seconds")
        return self._parse_uptime_seconds(up_time_seconds)

    @property
    def start_time(self) -> datetime:
        start_time = assert_attribute(self.response, "start_time")
        return datetime.strptime(start_time, self._START_TIME_FORMAT)

    @property
    def version(self) -> str:
        return self.assert_attribute("version")

    @property
    def device_type(self) -> DeviceType:
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
    def firstname(self) -> str:
        return self.assert_attribute("firstname")

    @property
    def lastname(self) -> str:
        return self.assert_attribute("lastname")

    @property
    def token(self) -> str:
        return self.assert_attribute("token")

    @property
    def roles(self) -> List[Roles]:
        return [Roles(role) for role in self.assert_attribute("roles")]

    @property
    def login_time(self):
        return self.assert_attribute("loginTime")


class Solar(Response):
    """
    Attributes
    - brand
    - model
    - power_rating_watts
    """

    @property
    def brand(self) -> str:
        return self.assert_attribute("brand")

    @property
    def model(self) -> str:
        return self.assert_attribute("model")

    @property
    def power_rating_watts(self) -> int:
        return self.assert_attribute("power_rating_watts")


class Battery(Response):
    @property
    def part_number(self) -> str:
        return self.assert_attribute("PackagePartNumber")

    @property
    def serial_number(self) -> str:
        return self.assert_attribute("PackageSerialNumber")

    @property
    def energy_charged(self) -> int:
        """get the amount of energy that was ever charged

        Returns:
            int: energy in watts
        """
        return self.assert_attribute("energy_charged")

    @property
    def energy_discharged(self) -> int:
        """get the amount of energy that was ever discharged

        Returns:
            int: energy in watts
        """
        return self.assert_attribute("energy_discharged")

    @property
    def energy_remaining(self) -> int:
        """get the remaining charged energy

        Returns:
            int: energy in watts
        """
        return self.assert_attribute("nominal_energy_remaining")

    @property
    def capacity(self) -> int:
        """get the capacity of a battery

        Returns:
            int: energy in watts
        """
        return self.assert_attribute("nominal_full_pack_energy")

    @property
    def wobble_detected(self) -> bool:
        """get whether a wobble was detected

        Returns:
            bool: detected
        """
        return self.assert_attribute("wobble_detected")
