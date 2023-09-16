import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .const import DEFAULT_KW_ROUND_PERSICION, DeviceType, MeterType, Roles
from .error import MeterNotAvailableError
from .helpers import convert_to_kw


@dataclass
class ResponseBase:
    _raw: dict

    def __repr__(self) -> str:
        return str(self._raw)


@dataclass
class MeterResponse(ResponseBase):
    meter: MeterType
    instant_power: float
    last_communication_time: str
    frequency: float
    energy_exported: float
    energy_imported: float
    instant_total_current: float
    instant_average_voltage: float

    @staticmethod
    def from_dict(meter: MeterType, src: dict) -> "MeterResponse":
        return MeterResponse(
            src,
            meter=meter,
            instant_power=src["instant_power"],
            last_communication_time=src["last_communication_time"],
            frequency=src["frequency"],
            energy_exported=src["energy_exported"],
            energy_imported=src["energy_imported"],
            instant_total_current=src["instant_total_current"],
            instant_average_voltage=src["instant_average_voltage"],
        )

    def get_energy_exported(self, precision=DEFAULT_KW_ROUND_PERSICION) -> float:
        return convert_to_kw(self.energy_exported, precision)

    def get_energy_imported(self, precision=DEFAULT_KW_ROUND_PERSICION) -> float:
        return convert_to_kw(self.energy_imported, precision)

    def get_instant_total_current(self, precision=DEFAULT_KW_ROUND_PERSICION) -> float:
        return round(self.instant_total_current, precision)

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


@dataclass
class MeterDetailsReadings(MeterResponse):
    real_power_a: Optional[float]
    real_power_b: Optional[float]
    real_power_c: Optional[float]

    i_a_current: Optional[float]
    i_b_current: Optional[float]
    i_c_current: Optional[float]

    v_l1n: Optional[float]
    v_l2n: Optional[float]
    v_l3n: Optional[float]

    @staticmethod
    def from_dict(meter: MeterType, src: dict) -> "MeterDetailsReadings":
        meter_response = MeterResponse.from_dict(meter, src)
        return MeterDetailsReadings(
            real_power_a=src.get("real_power_a"),
            real_power_b=src.get("real_power_b"),
            real_power_c=src.get("real_power_c"),
            i_a_current=src.get("i_a_current"),
            i_b_current=src.get("i_b_current"),
            i_c_current=src.get("i_c_current"),
            v_l1n=src.get("v_l1n"),
            v_l2n=src.get("v_l2n"),
            v_l3n=src.get("v_l3n"),
            # Populate with the values from the base class
            **meter_response.__dict__
        )


@dataclass
class MeterDetailsResponse(ResponseBase):
    location: MeterType
    readings: MeterDetailsReadings

    @staticmethod
    def from_dict(src: dict) -> "MeterDetailsResponse":
        location = MeterType(src["location"])
        readings = MeterDetailsReadings.from_dict(location, src["Cached_readings"])
        return MeterDetailsResponse(src, location=location, readings=readings)


class MetersAggregatesResponse(ResponseBase):
    @staticmethod
    def from_dict(src: dict) -> "MetersAggregatesResponse":
        meters = {
            MeterType(key): MeterResponse.from_dict(MeterType(key), value)
            for key, value in src.items()
        }
        return MetersAggregatesResponse(src, meters)

    def __init__(self, response: dict, meters: Dict[MeterType, MeterResponse]) -> None:
        self._raw = response
        self.meters = meters

    def __getattribute__(self, attr) -> Any:
        if attr.upper() in MeterType.__dict__:
            m = MeterType(attr)
            if m in self.meters:
                return self.meters[m]
            else:
                raise MeterNotAvailableError(m, list(self.meters.keys()))
        else:
            return object.__getattribute__(self, attr)

    def get_meter(self, meter: MeterType) -> Optional[MeterResponse]:
        return self.meters.get(meter)


@dataclass
class SiteMasterResponse(ResponseBase):
    status: str
    is_running: bool
    is_connected_to_tesla: bool
    is_power_supply_mode: bool

    @staticmethod
    def from_dict(src: dict) -> "SiteMasterResponse":
        return SiteMasterResponse(
            src,
            status=src["status"],
            is_running=src["running"],
            is_connected_to_tesla=src["connected_to_tesla"],
            is_power_supply_mode=src["power_supply_mode"],
        )


@dataclass
class SiteInfoResponse(ResponseBase):
    nominal_system_energy: int
    nominal_system_power: int
    site_name: str
    timezone: str

    @staticmethod
    def from_dict(src: dict) -> "SiteInfoResponse":
        return SiteInfoResponse(
            src,
            nominal_system_energy=src["nominal_system_energy_kWh"],
            nominal_system_power=src["nominal_system_power_kW"],
            site_name=src["site_name"],
            timezone=src["timezone"],
        )


@dataclass
class PowerwallStatusResponse(ResponseBase):
    start_time: datetime
    up_time_seconds: timedelta
    version: str
    device_type: DeviceType
    commission_count: int
    sync_type: str
    git_hash: str

    _START_TIME_FORMAT = "%Y-%m-%d %H:%M:%S %z"
    _UP_TIME_SECONDS_REGEX = re.compile(
        r"^((?P<days>[\.\d]+?)d)?((?P<hours>[\.\d]+?)h)?((?P<minutes>[\.\d]+?)m)?((?P<seconds>[\.\d]+?)s)?$"
    )

    @staticmethod
    def _parse_uptime_seconds(up_time_seconds: str) -> timedelta:
        match = PowerwallStatusResponse._UP_TIME_SECONDS_REGEX.match(up_time_seconds)
        if not match:
            raise ValueError(
                "Unable to parse up time seconds {}".format(up_time_seconds)
            )

        time_params = {}
        for name, param in match.groupdict().items():
            if param:
                time_params[name] = float(param)

        return timedelta(**time_params)

    @staticmethod
    def from_dict(src: dict) -> "PowerwallStatusResponse":
        start_time = datetime.strptime(
            src["start_time"], PowerwallStatusResponse._START_TIME_FORMAT
        )
        up_time_seconds = PowerwallStatusResponse._parse_uptime_seconds(
            src["up_time_seconds"]
        )
        return PowerwallStatusResponse(
            src,
            start_time=start_time,
            up_time_seconds=up_time_seconds,
            version=src["version"],
            device_type=DeviceType(src["device_type"]),
            commission_count=src["commission_count"],
            sync_type=src["sync_type"],
            git_hash=src["git_hash"],
        )


@dataclass
class LoginResponse(ResponseBase):
    firstname: str
    lastname: str
    token: str
    roles: List[Roles]
    login_time: str

    @staticmethod
    def from_dict(src: dict) -> "LoginResponse":
        return LoginResponse(
            src,
            firstname=src["firstname"],
            lastname=src["lastname"],
            token=src["token"],
            roles=[Roles(role) for role in src["roles"]],
            login_time=src["loginTime"],
        )


@dataclass
class SolarResponse(ResponseBase):
    brand: str
    model: str
    power_rating_watts: int

    @staticmethod
    def from_dict(src: dict) -> "SolarResponse":
        return SolarResponse(
            src,
            brand=src["brand"],
            model=src["model"],
            power_rating_watts=src["power_rating_watts"],
        )


@dataclass
class BatteryResponse(ResponseBase):
    part_number: str
    serial_number: str
    energy_charged: int
    energy_discharged: int
    energy_remaining: int
    capacity: int
    wobble_detected: bool

    @staticmethod
    def from_dict(src: dict) -> "BatteryResponse":
        return BatteryResponse(
            src,
            part_number=src["PackagePartNumber"],
            serial_number=src["PackageSerialNumber"],
            energy_charged=src["energy_charged"],
            energy_discharged=src["energy_discharged"],
            energy_remaining=src["nominal_energy_remaining"],
            capacity=src["nominal_full_pack_energy"],
            wobble_detected=src["wobble_detected"],
        )
