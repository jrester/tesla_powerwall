# Python Tesla Powerwall API

Python Tesla Powerwall API for consuming a local endpoint.

> Note: This is not an official API and as such might be incomplete and fail at any time

## Installation

```
$ pip install tesla_powerwall
```

## Usage

### Setup connection

```python3
from tesla_powerwall import Powerwall, User

power_wall = Powerwall("<ip of your Powerwall>")
#=> <Powerwall: ...>

# Login as customer
power_wall.login(User.CUSTOMER, "<email>", "<password>)
#=> <LoginResponse: ...>

# Check if we are really logged in 
power_wall.is_authenticated()
#=> True
```

> Note: By default the API client does not verify the SSL Certificate of the Powerwall. If you want to verify the SSL Certificate you can set `verify_ssl` to `True`.
> Also the API client suppresses warnings about an inseucre request (because we aren't verifing the certificate). If you want to enable those warnings you can set `disable_insecure_warning` to `False`

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

### Current power supply/draw

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

### Powerwall Mode and backup reserve percentage

Get current mode. Returns one of these: `OPERATION_MODE_SELF_CONSUMPTION`, `OPERATION_MODE_BACKUP`, `OPERATION_MODE_TIME_OF_USE`, `OPERATION_MODE_SCHEDULER`

```python3
power_wall.mode
#=> "self_consumption"

power_wall.set_mode(tesla_powerwall.OPERATION_MODE_BACKUP)

power_wall.backup_reserve_percentage
#=> 24.6

power_wall.set_backup_reserve_percentage(tesla_powerwall.BACKUP_RESERVE_PERCENTAGE_30)

power_wall.set_mode_and_backup_reserve_percentage(tesla_powerwall.OPERATION_MODE_BACKUP, tesla_powerwall.BACKUP_RESERVE_PERCENTAGE_30)
```
