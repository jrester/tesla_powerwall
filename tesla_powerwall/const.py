from enum import Enum

SUPPORTED_POWERWALL_VERSIONS = ["1.45.0", "1.45.1", "1.45.2"]
SUPPORTED_POWERWALL_GIT_HASHES = [""]

DEFAULT_KW_ROUND_PERSICION = 1


class User(Enum):
    INSTALLER = "installer"
    CUSTOMER = "customer"
    ENGINEER = "engineer"
    KIOSK = "kiosk"
    ADMIN = "admin"


class Roles(Enum):
    HOME_OWNER = "Home_Owner"
    KIOSK_VIEWER = "Kiosk_Viewer"
    PROVIDER_ENGINEER = "Provider_Engineer"
    TESLA_ENGINEER = "Tesla_Engineer"


class GridStatus(Enum):
    CONNECTED = "SystemGridConnected"
    ISLANEDED_READY = "SystemIslandedReady"
    ISLANEDED = "SystemIslandedActive"


class GridState(Enum):
    COMPLIANT = "Grid_Compliant"
    QUALIFINY = "Grid_Qualifying"
    UNCOMPLIANT = "Grid_Uncompliant"


class LineStatus(Enum):
    NON_BACKUP = "NonBackup"
    BACKUP = "Backup"
    NOT_CONFIGURED = "NotConfigured"


class OperationMode(Enum):
    BACKUP = "backup"
    SELF_CONSUMPTION = "self_consumption"
    AUTONOMOUS = "autonomous"
    SCHEDULER = "scheduler"
    SITE_CONTROL = "site_control"


SUPPORTED_OPERATION_MODES = [
    OperationMode.BACKUP,
    OperationMode.SELF_CONSUMPTION,
    OperationMode.AUTONOMOUS,
]


class InterfaceType(Enum):
    ETH = "EthType"
    GSM = "GsmType"
    WIFI = "WifiType"


class MeterType(Enum):
    SOLAR = "solar"
    SITE = "site"
    BATTERY = "battery"
    LOAD = "load"


class DeviceType(Enum):
    """
    Devicetype as returned by "device_type"
    GW1: Gateway 1
    GW2: Gateway 2
    SMC: ?
    """

    GW1 = "hec"
    GW2 = "teg"
    SMC = "smc"
