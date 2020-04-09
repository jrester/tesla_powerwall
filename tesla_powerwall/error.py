class ApiError(Exception):
    def __init__(self, error):
        super().__init__(f"Powerwall api error: {error}")


class PowerwallUnreachableError(Exception):
    def __init__(self):
        super().__init__(f"Powerwall is unreachable!")


class AccessDeniedError(Exception):
    def __init__(self, resource, error=None):
        msg = f"Access denied for resource {resource}"
        if msg is not None:
            msg = f"{msg}: {error}"
        super().__init__(msg)
