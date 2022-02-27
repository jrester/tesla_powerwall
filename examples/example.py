import os
from tesla_powerwall import Powerwall, Meter


def getenv(var):
    val = os.getenv(var)
    if val is None:
        raise ValueError(f"{var} must be set")
    return val


def print_meter_row(meter_data: Meter):
    print(
        "{:>8} {:>8} {:>17} {:>17} {!r:>8} {!r:>17} {!r:>17}".format(
            meter_data.meter.value,
            meter_data.get_power(),
            meter_data.get_energy_exported(),
            meter_data.get_energy_imported(),
            meter_data.is_active(),
            meter_data.is_drawing_from(),
            meter_data.is_sending_to(),
        )
    )


ip = getenv("POWERWALL_IP")
password = getenv("POWERWALL_PASSWORD")

power_wall = Powerwall(ip)
power_wall.login(password)
site_name = power_wall.get_site_info().site_name
meters_agg = power_wall.get_meters()

print(f"{site_name}:\n")

row_format = "{:>18}: {}"

values = [
    ("Charge (%)", round(power_wall.get_charge())),
    ("Capacity", power_wall.get_capacity()),
    ("Nominal Energy", power_wall.get_energy()),
    ("Grid Status", power_wall.get_grid_status().value),
    ("Backup Reserve (%)", round(power_wall.get_backup_reserve_percentage())),
    ("Device Type", power_wall.get_device_type().value),
    ("Software Version", power_wall.get_version())
]


for val in values:
    print(row_format.format(*val))

print("\n")

print(
    "{:>8} {:>8} {:>17} {:>17} {:>8} {:>17} {:>17}".format(
        "Meter",
        "Power",
        "Energy exported",
        "Energy imported",
        "Active",
        "Drawing from",
        "Sending to",
    )
)
for meter in meters_agg.meters:
    print_meter_row(meters_agg.get_meter(meter))
