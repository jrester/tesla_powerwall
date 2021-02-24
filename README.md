# Python Tesla Powerwall API <!-- omit in TOC -->

![Licence](https://img.shields.io/github/license/jrester/tesla_powerwall?style=for-the-badge)
![PyPI - Downloads](https://img.shields.io/pypi/dm/tesla_powerwall?color=blue&style=for-the-badge)
![PyPI](https://img.shields.io/pypi/v/tesla_powerwall?style=for-the-badge)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/tesla_powerwall?style=for-the-badge)

Python Tesla Powerwall API for consuming a local endpoint. The API is by no means complete and mainly features methods which are considered to be of common use. If you feel like methods should be included you are welcome to open an Issue or create a Pull Request.

> Note: This is not an official API provided by Tesla and as such might fail at any time.

Powerwall Software versions from 1.45.0 to 1.50.1 as well as 20.40 to 20.49 are tested, but others will probably work too. If you encounter an error regarding a change in the API of the Powerwall because your Powerwall has a different version than listed here please open an Issue to report this change so it can be fixed.

> For more information about versioning see [API versioning](#api-versioning).


# Table of Contents <!-- omit in TOC -->

- [Installation](#installation)
- [Usage](#usage)
  - [Setup](#setup)
  - [Authentication](#authentication)
  - [General](#general)
    - [API versioning](#api-versioning)
    - [Errors](#errors)
    - [Response](#response)
  - [Battery level](#battery-level)
  - [Powerwall Status](#powerwall-status)
  - [Sitemaster](#sitemaster)
  - [Siteinfo](#siteinfo)
  - [Meters](#meters)
    - [Aggregates](#aggregates)
    - [Current power supply/draw](#current-power-supplydraw)
    - [Energy exported/imported](#energy-exportedimported)
  - [Device Type](#device-type)
  - [Grid Status](#grid-status)
  - [Operation mode](#operation-mode)
  - [Powerwalls Serial Numbers](#powerwalls-serial-numbers)
  - [VIN](#vin)

## Installation

Install the library via pip:

```bash
$ pip install tesla_powerwall
```

## Usage

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
    # Provide a requests.Session
    http_sesion=None,
    # Whether to verify the SSL certificate or not
    verify_ssl=False,
    disable_insecure_warning=True,
    # Set the API to expect a specific version of the powerwall software
    pin_version=None
)
#=> <Powerwall ...>
```

> Note: By default the API client does not verify the SSL certificate of the Powerwall. If you want to verify the SSL certificate you can set `verify_ssl` to `True`.
> The API client suppresses warnings about an inseucre request (because we aren't verifing the certificate). If you want to enable those warnings you can set `disable_insecure_warning` to `False`.

### Authentication

Since version 20.49.0 authentication is required for all methods. For that reason you must call `login` before making a request to the API.
When you perform a request without being loggedin a `AccessDeniedError` will probably be thrown if the endpoint requires authentication.

To login you can either use `login` or `login_as`. `login` logs you in as `User.CUSTOMER` whereas with `login_as` you can choose a different user:

```python
from tesla_powerwall import User

# Login as customer without email
# The default value for the email is ""
powerwall.login("<password>")
#=> <LoginResponse ...>

# Login as customer with email
powerwall.login("<password>", "<email>")
#=> <LoginResponse ...>

# Login with different user
powerwall.login_as(User.INSTALLER, "<password>", "<email>")
#=> <LoginResponse ...>

# Check if we are logged in
# This method only checks wether a cookie with a Bearer token exists
# It does not verify whether this token is valid
powerwall.is_authenticated()
#=> True

# Logout
powerwall.logout()
```

### General

The API object directly maps the REST endpoints with a python method in the form of `<verb>_<path>`. So if you need the raw json responses you can use the API object. It can be either created manually or retrived from an existing `Powerwall`:

```python
from tesla_powerwall import API

# Manually create API object
api = API('https://<ip>/')
# Perform get on 'system_status/soe'
api.get_system_status_soe()
#=> {'percentage': 97.59281925744594}

# From existing powerwall
api = powerwall.get_api()
api.get_system_status_soe()
```

The `Powerwall` objet provides a wrapper around the API and exposes common methods.

#### API versioning

The powerwall API is inconsistent across different versions. This is why some versions may return different responses. If no version is specified the newest version is assumed.

If you are sure which version your powerwall has you can pin the Powerwall object to a version:

```python
from tesla_powerwall import Version
# Pin powerwall object
powerwall = Powerwall("<powerwall-ip>", pin_version="1.50.1")

# You can also pin a version after the powerwall object was created
powerwall.pin_version("20.40.3")
```

Otherwise you can let the API try to detect the version and pin it. This method should be prefered over the manual detection and pinning of the version:
```python
powerwall.detect_and_pin_version()
```

#### Errors

As the powerwall REST API varies widley between version and country it may happen that an attribute may not be included in your response. If that is the case a `MissingAttributeError` will be thrown indicating what attribute wasn't available. 

#### Response

Responses are usally wrapped inside a `Response` object to provide convenience methods. An Example is the `Meter` class which is a sublass of `Response`. Each `Response` object includes the `response` member which consists of the plain json response. 

```python
from helpers import assert_attribute

status = powerwall.get_status()
#=> <PowerwallStatus ...>

status.version
# is the same as
assert_attribute(status.response, "version")
# or
status.assert_attribute("version)
```

### Battery level

Get charge in percent:

```python
powerwall.get_charge()
#=> 97.59281925744594
```

### Powerwall Status

```python
status = powerwall.get_status()
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
sm = powerwall.sitemaster 
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
info = powerwall.get_site_info()
#=> <SiteInfo ...>
info.site_name
#=> 'Tesla Home'
info.country
#=> 'Germany'
info.nominal_system_energy
#=> 13.5
info.timezone
#=> 'Europe/Berlin'
```

### Meters

#### Aggregates

```python
from tesla_powerwall import MeterType

meters = powerwall.get_meters()
#=> <MetersAggregates ...>
meters.solar
#=> <Meter ...>

meters.get_meter(MeterType.SOLAR)
#=> <Meter ...>
```

Available meters are: `solar`, `site`, `load` and `battery`

#### Current power supply/draw

`Meter` provides different methods for checking current power supply/draw:

```python
meters = powerwall.get_meters()
meters.solar.get_power()
#=> 0.4 (in kWh)
meters.solar.instant_power
#=> 409.941801071167 (in watts)
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

`Meter.get_power` is just a convenience method which is equivalent to:

```python
from tesla_powerwall.helpers import convert_to_kw

convert_to_kw(meters.solar.instant_power, precision=1)
```

#### Energy exported/imported

Get energy exported/imported in watts with `energy_exported` and `energy_imported`. For the values in kWh use `get_energy_exported` and `get_energy_imported`:

```python
meters.battery.energy_exported
#=> 6394100
meters.battery.get_energy_exported()
#=> 6394.1
meters.battery.energy_imported
#=> 7576570
meters.battery.get_energy_imported()
#=> 7576.6
```

### Device Type

```python
powerwall.get_devie_type()
#=> <DeviceType.GW1: 'hec'>
```

### Grid Status

Get current grid status. 

```python
powerwall.get_grid_status()
#=> <GridStatus.Connected: 'SystemGridConnected'>
powerwall.get_grid_services_active()
#=> False
```

### Operation mode

```python
powerwall.get_operation_mode()
#=> <OperationMode.SELF_CONSUMPTION: ...>
powerwall.get_backup_reserve_percentage()
#=> 5.000019999999999
```

### Powerwalls Serial Numbers

```python
serials = powerwall.get_serial_numbers()
#=> ["...", "...", ...]
```

### VIN

```python
vin = powerwall.get_vin()
```