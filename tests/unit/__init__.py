import json
from pathlib import Path

ENDPOINT = "https://1.1.1.1/api/"

FIXTURE_BASE_PATH = Path("tests/unit/fixtures")


def load_fixture(name: str):
    path = FIXTURE_BASE_PATH / name
    with open(path) as f:
        return json.load(f)


GRID_STATUS_RESPONSE = load_fixture("grid_status.json")
ISLANDING_MODE_OFFGRID_RESPONSE = load_fixture("islanding_mode_offgrid.json")
ISLANDING_MODE_ONGRID_RESPONSE = load_fixture("islanding_mode_ongrid.json")
METER_SITE_RESPONSE = load_fixture("meter_site.json")
METER_SOLAR_RESPONSE = load_fixture("meter_solar.json")
METERS_AGGREGATES_RESPONSE = load_fixture("meters_aggregates.json")
OPERATION_RESPONSE = load_fixture("operation.json")
POWERWALLS_RESPONSE = load_fixture("powerwalls.json")
SITE_INFO_RESPONSE = load_fixture("site_info.json")
SITEMASTER_RESPONSE = load_fixture("sitemaster.json")
STATUS_RESPONSE = load_fixture("status.json")
SYSTEM_STATUS_RESPONSE = load_fixture("system_status.json")
