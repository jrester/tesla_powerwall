import os

from tesla_powerwall import Powerwall

ip = os.getenv("POWERWALL_IP")
if ip is None:
    raise ValueError("POWERWALL_IP must be set")

email = os.getenv("POWERWALL_EMAIL")
password = os.getenv("POWERWALL_PASSWORD")

power_wall = Powerwall(ip)

# Identify the powerwall version
power_wall.detect_and_pin_version()
print("Detected and pinned version: {}".format(power_wall.get_pinned_version()))

print("Current charge: {}".format(power_wall.get_charge()))
print("Device Type: {}".format(power_wall.get_device_type()))
