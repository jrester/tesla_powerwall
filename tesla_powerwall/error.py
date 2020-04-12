class PowerwallError(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class ApiError(PowerwallError):
    def __init__(self, error):
        super().__init__(f"Powerwall api error: {error}")


class PowerwallUnreachableError(PowerwallError):
    def __init__(self, reason=None):
        msg = f"Powerwall is unreachable"
        if reason is not None:
            self.reason = reason
            msg = f"{msg}: {reason}"
        super().__init__(msg)


class AccessDeniedError(PowerwallError):
    def __init__(self, resource, error=None):
        msg = f"Access denied for resource {resource}"
        if error is not None:
            msg = f"{msg}: {error}"
        super().__init__(msg)
