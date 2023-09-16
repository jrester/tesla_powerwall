from typing import List, Union

from .const import MeterType


class PowerwallError(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class ApiError(PowerwallError):
    def __init__(self, error: str):
        super().__init__("Powerwall api error: {}".format(error))


class MissingAttributeError(ApiError):
    def __init__(self, response: dict, attribute: str, url: Union[str, None] = None):
        self.response: dict = response
        self.attribute: str = attribute
        self.url: Union[str, None] = url

        if url is None:
            super().__init__(
                "The attribute '{}' is expected in the response but is missing.".format(
                    attribute
                )
            )
        else:
            super().__init__(
                "The attribute '{}' is expected in the response for \
                 '{}' but is missing.".format(
                    attribute, url
                )
            )


class PowerwallUnreachableError(PowerwallError):
    def __init__(self, reason: Union[str, None] = None):
        msg = "Powerwall is unreachable"
        self.reason: Union[str, None] = reason
        if reason is not None:
            msg = "{}: {}".format(msg, reason)
        super().__init__(msg)


class AccessDeniedError(PowerwallError):
    def __init__(
        self,
        resource: str,
        error: Union[str, None] = None,
        message: Union[str, None] = None,
    ):
        self.resource: str = resource
        self.error: Union[str, None] = error
        self.message: Union[str, None] = message
        msg = "Access denied for resource {}".format(resource)
        if error is not None:
            if message is not None:
                msg = "{}: {}: {}".format(msg, error, message)
            else:
                msg = "{}: {}".format(msg, error)
        super().__init__(msg)


class MeterNotAvailableError(PowerwallError):
    def __init__(self, meter: MeterType, available_meters: List[MeterType]):
        self.meter: MeterType = meter
        self.available_meters: List[MeterType] = available_meters
        super().__init__(
            "Meter {} is not available at your powerwall. \
             Following meters are available: {} ".format(
                meter.value, available_meters
            )
        )
