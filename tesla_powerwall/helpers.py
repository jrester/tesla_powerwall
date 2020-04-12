def convert_to_kw(value, rounded=True) -> float:
    """Converts watt to kilowatt and optionally round the value"""
    temp = value / 1000
    if rounded:
        return round(temp, 1)
    else:
        return temp
