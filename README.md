# Python tesla powerwall API

Python Tesla Powerwall API based on the [documentation](https://github.com/vloschiavo/powerwall2) by Vince Loschiavo.

## Usage

### Setup connection

```python3
from tesla_powerwall import PowerWall

# Without authentication
power_wall = PowerWall("<ip of your powerwall>")

# With authentication
power_wall = PowerWall("<ip of your powerwall>", "password")

```

### Current battery level

```python3
power_wall.charge
#=> 70.0
```

### Current power supply/draw

Get current power supply/draw for home, solar, battery and grid

```python3
power_wall.battery_power
#=> -2350
power_wall.grid_power
#=> -21.449996948242188
```

If you want to know wether you are drawing or sending you can use `is_sending_to_{battery, solar, grid}` and `is_drawing_from_{battery, solar, grid}`.
> Note: sending to solar occasionly happens at night as you can see in the documentation

### Grid Status

Get current grid status. Returns one of these: `GRID_STATUS_SYSTEM_GRID_UP`, `GRID_STATUS_SYSTEM_GRID_DOWN`, `GRID_STATUS_SYSTEM_GRID_RESTORED_NO_SYNC`.

```python3
power_wall.grid_status
#=> "SystemGridConnected"
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
