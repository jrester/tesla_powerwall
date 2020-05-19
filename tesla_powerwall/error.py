class PowerwallError(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class APIError(PowerwallError):
    def __init__(self, error):
        super().__init__("Powerwall api error: {}".format(error))


class APIChangedError(APIError):
    def __init__(self, response_class, json_response, added_attrs=[], removed_attrs=[]):
        self.json_response = json_response
        self.response_class = response_class
        self.added_attrs = added_attrs
        self.removed_attrs = removed_attrs

        msg = self._construct_msg()

        super().__init__(msg)

    def _construct_msg(self):
        msg = "It seems like the Powerwall API changed for '{}''".format(self.response_class)
        if len(self.added_attrs) > 0:
            if len(self.removed_attrs) > 0:
                msg = "{}: Attributes added: {}, removed attributes {}".format(msg, self.added_attrs, self.removed_attrs)
            else:
                msg = "{}: Some attributes have been added to the response: {}".format(msg, self.added_attrs)
        elif len(self.removed_attrs) > 0:
            msg = "{}: Some attributes have been removed from the response: {}".format(msg, self.removed_attrs)
        return msg


class PowerwallUnreachableError(PowerwallError):
    def __init__(self, reason=None):
        msg = "Powerwall is unreachable"
        self.reason = reason
        if reason is not None:
            msg = "{}: {}".format(msg, reason)
        super().__init__(msg)


class AccessDeniedError(PowerwallError):
    def __init__(self, resource, error=None):
        self.resource = resource
        self.error = error
        msg = "Access denied for resource {}".format(resource)
        if error is not None:
            msg = "{}: {}".format(msg, error)
        super().__init__(msg)
