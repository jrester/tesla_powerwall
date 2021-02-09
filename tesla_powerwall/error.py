class PowerwallError(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class APIError(PowerwallError):
    def __init__(self, error):
        super().__init__("Powerwall api error: {}".format(error))


class MissingAttributeError(APIError):
    def __init__(self, response: dict, attribute: str, url: str = None):
        self.response = response
        self.attribute = attribute
        self.url = url

        if url is None:
            super().__init__(
                "The attribute '{}' is expected in the response but is missing.".format(
                    attribute
                )
            )
        else:
            super().__init__(
                "The attribute '{}' is expected in the response for '{}' but is missing.".format(
                    attribute, url
                )
            )


class PowerwallUnreachableError(PowerwallError):
    def __init__(self, reason=None):
        msg = "Powerwall is unreachable"
        self.reason = reason
        if reason is not None:
            msg = "{}: {}".format(msg, reason)
        super().__init__(msg)


class AccessDeniedError(PowerwallError):
    def __init__(self, resource, error=None, message=None):
        self.resource = resource
        self.error = error
        self.message = message
        msg = "Access denied for resource {}".format(resource)
        if error is not None:
            if message is not None:
                msg = "{}: {}: {}".format(msg, error, message)
            else:
                msg = "{}: {}".format(msg, error)
        super().__init__(msg)
