# Python Tesla Powerwall API

Python Tesla Powerwall API for consuming a local endpoint.

> Note: This is not an official API and as such might be incomplete and fail at any time

## Installation

```
$ pip install tesla_powerwall
```

## Usage

### Setup connection and authentication

```python3
from tesla_powerwall import Powerwall

power_wall = Powerwall("<ip of your Powerwall>")
#=> <Powerwall: ...>
```

> Note: By default the API client does not verify the SSL Certificate of the Powerwall. If you want to verify the SSL Certificate you can set `verify_ssl` to `True`.
> Also the API client suppresses warnings about an inseucre request (because we aren't verifing the certificate). If you want to enable those warnings you can set `disable_insecure_warning` to `False`

### Authentication

To login you can either use `login` or `login_as`. `login` logs you in as `User.CUSTOMER` whereas with `login_as` you can choose a different user:

```python3
from tesla_powerwall import User

# Login as customer
power_wall.login("<email>", "<password>)
#=> <LoginResponse: ...>

# Login with different user
power_wall.login_as(User.INSTALLER, "<email>", "<password>")
#=> <LoginResponse: ...>

# Check if we are logged in 
power_wall.is_authenticated()
#=> True

# Logout
power_wall.logout()
```

### Current battery level

Get charge in percent:

```python3
power_wall.get_charge()
#=> 98
```

The API also returns the exact percentage. You can get the exact percentage by passing `false` to `rounded`:

```python3
power_wall.get_charge(rounded=false)
#=> 97.59281925744594
```

### Powerwall Status

```python3
power_wall.get_status()
```

### Sitemaster

```python3
sm = power_wall.sitemaster 
#=> <tesla_powerwall.SiteMasterResponse ...>
sm.status 
#=> StatusUp
sm.running
#=> true
sm.connected_to_tesla
#=> true
```

### Meters

#### Aggregates


```python3 
power_wall.get_meters()
#=> <tesla_powerwall.MetersAggregateResponse>
#=> 
```

#### Details about meter

Returns details about the meter. When no details are available an empty dict is returned.

```python3
power_wall.meter_detailed(MeterType.SOLAR)
#=> [{'id': ...}, ...]
power_wall.meter_detailed(MeterType.LOAD)
#=> {}
```

#### Current power supply/draw

Get current power supply/draw for home, solar, battery and grid. 

```python3
power_wall.is_drawing_from(MeterType.SOLAR)
#=> True
power_wall.is_sending_to(MeterType.LOAD)
#=> True
power_wall.is_active(MeterType.BATTERY)
#=> False
power_wall.get_power(MeterType.SOLAR)
#=> 2.8 (in kWh)
```

Each of those methods are wrappers for their respective methods on `MetersResponse`. When you call those wrapper methods `get_meters()` is always called. So if you need to query multiple meters you should first retrive all meters and execute the respective methods on the response:

```python3
meters = power_wall.get_meters()
meters.solar.is_drawing_from()
#=> True
meters.load.is_sending_to()
#=> True
meters.battery.is_active()
#=> False
meters.solar.get_power()
#=> 2.8 (in kWh)
```

`get_power` is just a convenience method which is equivalent to:

```python3
from tesla_powerwall.helpers import convert_to_kwh

convert_to_kwh(meters.solar.instant_power, True)
```

### Device Type

```python3
power_wall.device_type
#=> <DeviceType.GW1: 'hec'>
```

### Grid Status

Get current grid status. 

```python3
power_wall.grid_status
#=> <GridStatus.Connected: 'SystemGridConnected'>
```

### Operation mode

```python3
power_wall.get_operation_mode()
#=> <OperationMode.SELF_CONSUMPTION: ...>
```

### Powerwall status

```python3
status = power_wall.get_status()
#=> <PowerwallStatusResponse ...>
status.version
#=> '1.45.2'
```

### More methods

* get_vin
* get_solars
* get_meters_info
* get_installer
* get_logs