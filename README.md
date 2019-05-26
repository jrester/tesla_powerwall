# Python tesla powerwall API

## Installation

```bash
git clone https://github.com/jrester/tesla_powerwall
```

```bash
cd tesla_powerwall && sudo python3 setup.py install
```

## Usage

```python3
from tesla_powerwall import PowerWall

power_wall = PowerWall("192.168.xxx.xxx")

power_wall.charge

```

For more information about the api see [here](https://github.com/vloschiavo/powerwall2).