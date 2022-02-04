# This is an Example of how to use the tesla_powerwall API and the influxdb Client to generate and store
# Monitoring Data in a Time Series Database. InfluxDB is natively compatible with https://grafana.com

#Imports
import os
from time import sleep
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS
from tesla_powerwall import Powerwall


# Variables
## InfluxDB
bucket = "<my-bucket>"
org = "<my-org>"
token = "<my-token>"
url="http://localhost:8086"

client = influxdb_client.InfluxDBClient(
    url=url,
    token=token,
    org=org
)

write_api = client.write_api(write_options=SYNCHRONOUS)

## Powerwall

ip = os.getenv("POWERWALL_IP")
if ip is None:
    raise ValueError("POWERWALL_IP must be set")

email = os.getenv("POWERWALL_EMAIL")
password = os.getenv("POWERWALL_PASSWORD")

power_wall = Powerwall(ip)

# Program
print("Current charge: {}".format(power_wall.get_charge()))
print("Device Type: {}".format(power_wall.get_device_type()))

## Sending Data

while True:
    p = influxdb_client.Point("Measurement").field("Charge", power_wall.get_charge)
    write_api.write(bucket=bucket, org=org, record = p)
    sleep(1)
