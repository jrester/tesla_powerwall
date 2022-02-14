from typing import Union

from .error import MissingAttributeError


def convert_to_kw(value: float, precision: int = 1) -> float:
    """Converts watt to kilowatt and rounds to precision"""
    # Don't round if precision is -1
    if precision == -1:
        return value / 1000
    else:
        return round(value / 1000, precision)


def assert_attribute(response: dict, attr: str, url: Union[str, None] = None):
    value = response.get(attr)
    if value is None:
        raise MissingAttributeError(response, attr, url)
    else:
        return value
