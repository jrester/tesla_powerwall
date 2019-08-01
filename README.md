# Python tesla powerwall API

For more information please refer to the documentation of the [powerwall rest api](https://github.com/vloschiavo/powerwall2)

## Usage

### Setup connection

```python3
from tesla_powerwall import PowerWall

power_wall = PowerWall("<ip of your powerwall>")

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

If you want to know wether you are drawing or sending you can use `sending_to_{battery, solar, grid}` and `drawing_from_{battery, solar, grid}`.
> Note: sending to solar occasionly happens at night as you can read in the documentation