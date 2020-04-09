from enum import Enum

STATUS_UP = "StatusUp"
STATUS_DOWN = 'StatusDown'

class User(Enum):
    INSTALLER = "installer"
    CUSTOMER = "customer"
    ENGINEER = "engineer"
    KIOSK = "kisok"
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
    OperationMode.AUTONOMOUS
]

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

# NOTE: Those values may be incorrect
BACKUP_RESERVE_PERCENTAGE_5 = 10
BACKUP_RESERVE_PERCENTAGE_16 = 20
BACKUP_RESERVE_PERCENTAGE_20 = 24
BACKUP_RESERVE_PERCENTAGE_21 = 24.6
BACKUP_RESERVE_PERCENTAGE_30 = 33
BACKUP_RESERVE_PERCENTAGE_100 = 100
