# Python Tesla Powerwall API

Python Tesla Powerwall API for consuming a local endpoint.

> Note: This is not an official API and as such might be incomplete and fail at any time
> The API was tested with powerwall version 1.45.2 but 1.45.0 and 1.45.1 should also work. 

## Installation

```bash
$ pip install tesla_powerwall
```

## Usage

### Setup connection

```python
from tesla_powerwall import Powerwall

power_wall = Powerwall("<ip of your Powerwall>")
#=> <Powerwall ...>
```

> Note: By default the API client does not verify the SSL Certificate of the Powerwall. If you want to verify the SSL Certificate you can set `verify_ssl` to `True`.
> Also the API client suppresses warnings about an inseucre request (because we aren't verifing the certificate). If you want to enable those warnings you can set `disable_insecure_warning` to `False`

### Authentication

To login you can either use `login` or `login_as`. `login` logs you in as `User.CUSTOMER` whereas with `login_as` you can choose a different user:

```python
from tesla_powerwall import User

# Login as customer
power_wall.login("<email>", "<password>")
#=> <LoginResponse ...>

# Login with different user
power_wall.login_as(User.INSTALLER, "<email>", "<password>")
#=> <LoginResponse ...>

# Check if we are logged in 
power_wall.is_authenticated()
#=> True

# Logout
power_wall.logout()
```

### Current battery level

Get charge in percent:

```python
power_wall.get_charge()
#=> 98
```

The API also returns the exact percentage. You can get the exact percentage by passing `False` to `rounded`:

```python
power_wall.get_charge(rounded=False)
#=> 97.59281925744594
```

### Powerwall Status

```python
status = power_wall.get_status()
#=> <PowerwallStatusResponse ...>
status.version
#=> '1.45.2'
```

### Sitemaster

```python
sm = power_wall.sitemaster 
#=> <SiteMasterResponse ...>
sm.status 
#=> StatusUp
sm.running
#=> true
sm.connected_to_tesla
#=> true
```

### Siteinfo

```python
info = power_wall.get_site_info()
#=> <SiteInfoResponse ...>
info.site_name
#=> Tesla Home
info.country
#=> Germany
```

### Meters

#### Aggregates

```python
meters = power_wall.get_meters()
#=> <MetersAggregateResponse ...>
meters.solar
#=> <MetersResponse ...>
```

#### Details about meter

Returns details about the meter. When no details are available `None` is returned.

```python
power_wall.meter_detailed(MeterType.SOLAR)
#=> [<MeterDetailsResponse ...>]
power_wall.meter_detailed(MeterType.LOAD)
#=> None
```

#### Current power supply/draw

Get current power supply/draw for home, solar, battery and grid. 

```python
power_wall.is_drawing_from(MeterType.SOLAR)
#=> True
power_wall.is_sending_to(MeterType.LOAD)
#=> True
power_wall.is_active(MeterType.BATTERY)
#=> False
power_wall.get_power(MeterType.SOLAR)
#=> 2.8 (in kWh)
```

> Note: For MeterType.LOAD is_drawing_from **always** returns `False` because it cannot be drawn from `load`.

Each of those methods are wrappers for their respective methods on `MetersResponse`. When you call those wrapper methods `get_meters()` is always called. So if you need to query multiple meters you should first retrive all meters and execute the respective methods on the response:

```python
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

```python
from tesla_powerwall.helpers import convert_to_kw

convert_to_kw(meters.solar.instant_power, precision=1)
```

### Device Type

```python
power_wall.device_type
#=> <DeviceType.GW1: 'hec'>
```

### Grid Status

Get current grid status. 

```python
power_wall.get_grid_status()
#=> <GridStatus.Connected: 'SystemGridConnected'>
power_wall.get_grid_services_active()
#=> False
```

### Operation mode

```python
power_wall.get_operation_mode()
#=> <OperationMode.SELF_CONSUMPTION: ...>
```

### Powerwall status

```python
status = power_wall.get_status()
#=> <PowerwallStatusResponse ...>
status.version
#=> '1.45.2'

# If you just need the version you can also use `get_version`
power_wall.get_version()
#=> '1.45.2'
```

### Powerwalls

Get all powerwalls

```python
powerwalls_resp = power_wall.get_powerwalls()
#=> <ListPowerwallsResponse ...>
powerwalls_resp.powerwalls
#=> [{"Package...}]
```

Get powerwalls status when authenticated:

```python
powerwalls_status = power_wall.get_poweralls_status()
#=> <PowerwalllsStatusResponse ...>
```
For some unkown reason the response to `get_powerwalls` also includes the powerwalls status, so if you are not authenticated you can just retrive the status from the `ListPowerwallsResponse`

```python
powerwalls_resp = power_wall.get_powerwalls()
powerwalls_resp.status
#=> <PowerwallsStatusResponse ...>
```

### More

Most methods return a `Response` object except for those that only return a single value like `get_charge` and those that have to complex output like `get_networks`. 

Most times those `Response`s reflect the json response but for most nested data objects this is not the case.

Some other methods include:

* `get_vin`
* `get_solars`
* `get_meters_info`
* `get_installer_info`
* `get_meter_readings`
* `get_meters_info`
* `get_phase_usage`