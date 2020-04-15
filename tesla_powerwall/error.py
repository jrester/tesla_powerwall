class PowerwallError(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class ApiError(PowerwallError):
    def __init__(self, error):
        super().__init__(f"Powerwall api error: {error}")


class APIChangedError(ApiError):
    def __init__(self, response_class, json_response, added_attrs=[], removed_attrs=[]):
        self.json_response = json_response
        self.response_class = response_class
        self.added_attrs = added_attrs
        self.removed_attrs = removed_attrs

        msg = self._construct_msg()

        super().__init__(msg)

    def _construct_msg(self):
        msg = f"It seems like the Powerwall API changed for {self.response_class}"
        if len(self.added_attrs) > 0:
            if len(self.removed_attrs) > 0:
                msg = f"{msg}: Attributes added: {self.added_attrs}, removed attributes {self.removed_attrs}"
            else:
                msg = f"{msg}: Some attributes where added to the response: {self.added_attrs}"
        elif len(self.removed_attrs) > 0:
            msg = f"{msg}: Some attributes where removed from the response: {self.removed_attrs}"
        return msg


class PowerwallUnreachableError(PowerwallError):
    def __init__(self, reason=None):
        msg = f"Powerwall is unreachable"
        self.reason = reason
        if reason is not None:
            msg = f"{msg}: {reason}"
        super().__init__(msg)


class AccessDeniedError(PowerwallError):
    def __init__(self, resource, error=None):
        self.resource = resource
        self.error = error
        msg = f"Access denied for resource {resource}"
        if error is not None:
            msg = f"{msg}: {error}"
        super().__init__(msg)
