from datetime import datetime

from .const import MeterType

class Response(object):
    """Basic Response object that can be constructed from a json response"""
    def __init__(self, json_response : dict):
        self.json_response = json_response

        for attr in self.__class__._JSON_ATTRS:
            self._add_attr(attr)
            
    def _add_attr(self, attr : str):
        if attr in self.json_response:
            setattr(self, attr, self.json_response[attr])
        else:
            raise ValueError(
                f"Missing key {attr} in response from Powerwall. Either the Powerwall sent an invalid response or the API changed!")


class MetersAggregateResponse(Response):
    """
    Response for "meters/aggregates"
    """

    def __init__(self, json_response):
        for meter in MeterType:
            if meter.value in json_response:
                setattr(self, meter.value, 
                    MetersResponse(json_response[meter.value]))
                

class MetersResponse(Response):
    """Response for a single Meter
    Usually a nested item in the MetersAggregateResponse
    """
    _JSON_ATTRS = [
        "last_communication_time",
        "instant_power",                # The power that is supplied/drawn from the meter
        "instant_reactive_power", 
        "instant_apparent_power",       
        "frequency",
        "energy_exported",
        "energy_imported",
        "instant_average_voltage",
        "instant_total_current",
        "i_a_current",
        "i_b_current",
        "i_c_current",
        "timeout"
    ]

    def __init__(self, json_response : dict, meter=None):
        self.meter = meter

class SitemasterResponse(Response):
    _JSON_ATTRS = [
        "status",
        "running",
        "connected_to_tesla"
    ]


class SiteinfoResponse(Response):
    _JSON_ATTRS = [
        "max_site_meter_power_kW",
        "min_site_meter_power_kW",
        "nominal_system_energy_kWh",
        "nominal_system_power_kW",
        "max_system_energy_kWh",
        "max_system_power_kW",
        "site_name",
        "timezone",
        "grid_code",
        "grid_voltage_setting",
        "grid_freq_setting",
        "grid_phase_setting",
        "country",
        "state",
        "distributor",
        "utility",
        "retailer",
        "region"
    ]


class CustomerRegistrationResponse(Response):
    _JSON_ATTRS = [
        "privacy_notice",
        "limited_warranty",
        "grid_services",
        "marketing",
        "registered",
        "timed_out_registration"
    ]

class PowerwallStatusResponse(Response):
    _START_TIME_FORMAT = "%Y-%m-%d %H:%M:%S %z"

    _JSON_ATTRS = [
        "start_time",
        "up_time_seconds",  
        "is_new",
        "version",
        "git_hash"
    ]

    def __init__(self, json_response):
        json_response["start_time"] = datetime.strptime(
            json_response["start_time"], 
            PowerwallStatusResponse._START_TIME_FORMAT
        )
        # up_time_seconds is not realy given in seconds but rate
        # json_response["up_time_seconds"] = datetime.strptime(
        #     json_response["up_time_seconds"], StatusResponse._UP_TIMES_FORMAT
        # )
        super().__init__(json_response)

class PowerwallsStatusResponse(Response):
    _JSON_ATTRS = [
        "enumerating",
        "updating",
        "checking_if_offgrid",
        "running_phase_detection",
        "phase_detection_last_error",
        "bubble_shedding",
        "on_grid_check_error",
        "grid_qualifying",
        "grud_code_validating",
        "phase_detection_not_available"
    ]