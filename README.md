![Licence](https://img.shields.io/github/license/jrester/tesla_powerwall?style=for-the-badge)
![PyPI - Downloads](https://img.shields.io/pypi/dm/tesla_powerwall?color=blue&style=for-the-badge)
![PyPI](https://img.shields.io/pypi/v/tesla_powerwall?style=for-the-badge)

Python Tesla Powerwall API for consuming a local endpoint.
> Note: This is not an official API provided by Tesla and this project is not affilated with Tesla in any way.

Powerwall Software versions from 1.47.0 to 1.50.1 as well as 20.40 to 22.9.2 are tested, but others will probably work too.

# Table of Contents <!-- omit in TOC -->

- [Installation](#installation)
- [Limitations](#limitations)
    - [Adjusting Backup Reserve Percentage](#adjusting-backup-reserve-percentage)
- [Usage](#usage)
    - [Setup](#setup)
    - [Authentication](#authentication)
    - [General](#general)
        - [Errors](#errors)
        - [Response](#response)
    - [Battery level](#battery-level)
    - [Capacity](#capacity)
    - [Battery Packs](#battery-packs)
    - [Powerwall Status](#powerwall-status)
    - [Sitemaster](#sitemaster)
    - [Siteinfo](#siteinfo)
    - [Meters](#meters)
        - [Aggregates](#aggregates)
        - [Current power supply/draw](#current-power-supplydraw)
        - [Energy exported/imported](#energy-exportedimported)
        - [Details](#details)
    - [Device Type](#device-type)
    - [Grid Status](#grid-status)
    - [Operation mode](#operation-mode)
    - [Powerwalls Serial Numbers](#powerwalls-serial-numbers)
    - [Gateway DIN](#gateway-din)
    - [VIN](#vin)
    - [Off-grid status](#off-grid-status-set-island-mode)

## Installation

Install the library via pip:

```bash
$ pip install tesla_powerwall
```

## Limitations

### Adjusting Backup Reserve Percentage

Currently it is not possible to control the Backup Percentage, because you need to be logged in as installer, which requires physical switch toggle. There is an ongoing discussion about a possible solution [here](https://github.com/vloschiavo/powerwall2/issues/55).
However, if you believe there exists a solution, feel free to open an issue detailing the solution.

## Usage

For a basic Overview of the functionality of this library you can take a look at `examples/example.py`:

```bash
$ export POWERWALL_IP=<ip of your Powerwall>
$ export POWERWALL_PASSWORD=<your password>
$ python3 examples/example.py
```

### Setup

```python
from tesla_powerwall import Powerwall

# Create a simple powerwall object by providing the IP
powerwall = Powerwall("<ip of your Powerwall>")
#=> <Powerwall ...>

# Create a powerwall object with more options
powerwall = Powerwall(
    endpoint="<ip of your powerwall>",
    # Configure timeout; default is 10
    timeout=10,
    # Provide a requests.Session or None. If None is provided, a Session will be created.
    http_session=None,
    # Whether to verify the SSL certificate or not
    verify_ssl=False,
    disable_insecure_warning=True
)
#=> <Powerwall ...>
```

> Note: By default the API client does not verify the SSL certificate of the Powerwall. If you want to verify the SSL certificate you can set `verify_ssl` to `True`.
> The API client suppresses warnings about an inseucre request (because we aren't verifing the certificate). If you want to enable those warnings you can set `disable_insecure_warning` to `False`.

### Authentication

Since version 20.49.0 authentication is required for all methods. For that reason you must call `login` before making a request to the API.
When you perform a request without being authenticated, an `AccessDeniedError` will be thrown.

To login you can either use `login` or `login_as`. `login` logs you in as `User.CUSTOMER` whereas with `login_as` you can choose a different user:

```python
from tesla_powerwall import User

# Login as customer without email
# The default value for the email is ""
await powerwall.login("<password>")
#=> <LoginResponse ...>

# Login as customer with email
await powerwall.login("<password>", "<email>")
#=> <LoginResponse ...>

# Login with different user
await powerwall.login_as(User.INSTALLER, "<password>", "<email>")
#=> <LoginResponse ...>

# Check if we are logged in
# This method only checks wether a cookie with a Bearer token exists
# It does not verify whether this token is valid
powerwall.is_authenticated()
#=> True

# Logout
await powerwall.logout()
powerwall.is_authenticated()
#=> False
```

### General

The API object directly maps the REST endpoints with a python method in the form of `<verb>_<path>`. So if you need the raw json responses you can use the API object. It can be either created manually or retrived from an existing `Powerwall`:

```python
from tesla_powerwall import API

# Manually create API object
api = API('https://<ip>/')
# Perform get on 'system_status/soe'
await api.get_system_status_soe()
#=> {'percentage': 97.59281925744594}

# From existing powerwall
api = powerwall.get_api()
await api.get_system_status_soe()
```

The `Powerwall` objet provides a wrapper around the API and exposes common methods.

### Battery level

Get charge in percent:

```python
await powerwall.get_charge()
#=> 97.59281925744594 (%)
```

Get charge in watt:

```python
await powerwall.get_energy()
#=> 14807 (Wh)
```

### Capacity

Get the capacity of your powerwall in watt:

```python
await powerwall.get_capacity()
#=> 28078 (Wh)
```

### Battery Packs

Get information about the battery packs that are installed:

```python
batteries = await powerwall.get_batteries()
#=> [<Battery ...>, <Battery ...>]
batteries[0].part_number
#=> "XXX-G"
batteries[0].serial_number
#=> "TGXXX"
batteries[0].energy_remaining
#=> 7378 (Wh)
batteries[0].capacity
#=> 14031 (Wh)
batteries[0].energy_charged
#=> 5525740 (Wh)
batteries[0].energy_discharged
#=> 4659550 (Wh)
batteries[0].wobble_detected
#=> False
```

### Powerwall Status

```python
status = await powerwall.get_status()
#=> <PowerwallStatus ...>
status.version
#=> '1.49.0'
status.up_time_seconds
#=> datetime.timedelta(days=13, seconds=63287, microseconds=146455)
status.start_time
#=> datetime.datetime(2020, 9, 23, 23, 31, 16, tzinfo=datetime.timezone(datetime.timedelta(seconds=28800)))
status.device_type
#=> DeviceType.GW2
```

### Sitemaster

```python
sm = await powerwall.get_sitemaster()
#=> <SiteMaster ...>
sm.status
#=> StatusUp
sm.running
#=> true
sm.connected_to_tesla
#=> true
```

The sitemaster can be started and stopped using `run()` and `stop()`

### Siteinfo

```python
info = await powerwall.get_site_info()
#=> <SiteInfo ...>
info.site_name
#=> 'Tesla Home'
info.country
#=> 'Germany'
info.nominal_system_energy
#=> 13.5 (kWh)
info.timezone
#=> 'Europe/Berlin'
```

### Meters

#### Aggregates

```python
from tesla_powerwall import MeterType

meters = await powerwall.get_meters()
#=> <MetersAggregates ...>

# access meter, but may return None when meter is not available
meters.get_meter(MeterType.SOLAR)
#=> <Meter ...>

# access meter, but may raise MeterNotAvailableError when the meter is not available at your powerwall (e.g. no solar panels installed)
meters.solar
#=> <MeterResponse ...>

# get all available meters at the current powerwall
meters.meters.keys()
#=> [<MeterType.SITE: 'site'>, <MeterType.BATTERY: 'battery'>, <MeterType.LOAD: 'load'>, <MeterType.SOLAR: 'solar'>]
```

Available meters are: `solar`, `site`, `load`, `battery`, `generator`, and `busway`. Some of those meters might not be available based on the installation and raise MeterNotAvailableError when accessed.

#### Current power supply/draw

`Meter` provides different methods for checking current power supply/draw:

```python
meters = await powerwall.get_meters()
meters.solar.get_power()
#=> 0.4 (kW)
meters.solar.instant_power
#=> 409.941801071167 (W)
meters.solar.is_drawing_from()
#=> True
meters.load.is_sending_to()
#=> True
meters.battery.is_active()
#=> False

# Different precision settings might return different results
meters.battery.is_active(precision=5)
#=> True
```

> Note: For MeterType.LOAD `is_drawing_from` **always** returns `False` because it cannot be drawn from `load`.

#### Energy exported/imported

Get energy exported/imported in watt-hours (Wh) with `energy_exported` and `energy_imported`. For the values in kilowatt-hours (kWh) use `get_energy_exported` and `get_energy_imported`:

```python
meters.battery.energy_exported
#=> 6394100 (Wh)
meters.battery.get_energy_exported()
#=> 6394.1 (kWh)
meters.battery.energy_imported
#=> 7576570 (Wh)
meters.battery.get_energy_imported()
#=> 7576.6 (kWh)
```

### Details

You can receive more detailed information about the meters `site` and `solar`:

```python
meter_details = await powerwall.get_meter_site() # or get_meter_solar() for the solar meter
#=> <MeterDetailsResponse ...>
readings = meter_details.readings
#=> <MeterDetailsReadings ...>
readings.real_power_a # same for real_power_b and real_power_c
#=> 619.13532458
readings.i_a_current # same for i_b_current and i_c_current
#=> 3.02
readings.v_l1n # smae for v_l2n and v_l3n
#=> 235.82
readings.instant_power
#=> -18.000023458
readings.is_sending()
```

As `MeterDetailsReadings` inherits from `MeterResponse` (which is used in `MetersAggratesResponse`) it exposes the same data and methods.

> For the meters battery and grid no additional details are provided, therefore no methods exist for those meters

### Device Type

```python
await powerwall.get_device_type()
#=> <DeviceType.GW1: 'hec'>
```

### Grid Status

Get current grid status.

```python
await powerwall.get_grid_status()
#=> <GridStatus.Connected: 'SystemGridConnected'>
await powerwall.is_grid_services_active()
#=> False
```

### Operation mode

```python
await powerwall.get_operation_mode()
#=> <OperationMode.SELF_CONSUMPTION: ...>
await powerwall.get_backup_reserve_percentage()
#=> 5.000019999999999 (%)
```

### Powerwalls Serial Numbers

```python
await serials = powerwall.get_serial_numbers()
#=> ["...", "...", ...]
```

### Gateway DIN

```python
await din = powerwall.get_gateway_din()
#=> 4159645-02-A--TGXXX
```

### VIN

```python
await vin = powerwall.get_vin()
```

### Off-grid status (Set Island mode)

Take your powerwall on- and off-grid similar to the "Take off-grid" button in the Tesla app.

#### Set powerwall to off-grid (Islanded)

```python
await powerwall.set_island_mode(IslandMode.OFFGRID)
```

#### Set powerwall to off-grid (Connected)

```python
await powerwall.set_island_mode(IslandMode.ONGRID)
```

# Development

## Building

```sh
$ python -m build
```

## Testing

### Unit-Tests

To run unit tests use tox:

```sh
$ tox -e unit
```

### Integration-Tests

```sh
$ tox -e integration
```
