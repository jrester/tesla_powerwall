def convert_to_kw(value: float, precision: int = 1) -> float:
    """Converts watt to kilowatt and rounds to precision"""
    # Don't round if precision is -1
    if precision == -1:
        return value / 1000
    else:
        return round(value / 1000, precision)
