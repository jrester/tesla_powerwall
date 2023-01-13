from enum import Enum

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
    ISLANDED_READY = "SystemIslandedReady"
    ISLANDED = "SystemIslandedActive"
    TRANSITION_TO_GRID = "SystemTransitionToGrid"  # Used in version 1.46.0
    TRANSITION_TO_ISLAND = "SystemTransitionToIsland"

class IslandMode(Enum):
    OFFGRID = "intentional_reconnect_failsafe"
    ONGRID = "backup"

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
    GENERATOR = "generator"
    BUSWAY = "busway"


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


class SyncType(Enum):
    V1 = "v1"
    V2 = "v2"
    V2_1 = "v2.1"


class UpdateState(Enum):
    CHECKING = "/clear_update_status"
    SUCCEEDED = "/update_succeeded"
    FAILED = "/update_failed"
    STAGED = "/update_staged"
    DOWNLOAD = "/download"
    DOWNLOADED = "/update_downloaded"
    UNKNOWN = "/update_unknown"


class UpdateStatus(Enum):
    IGNORING = "ignoring"
    ERROR = "error"
    NONACTIONABLE = "nonactionable"
