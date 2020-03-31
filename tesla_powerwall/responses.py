class Response(object):
    def __init__(self, json_response):
        self.json_response = json_response

        for attr in self.__class__.JSON_ATTRS:
            if attr in json_response:
                setattr(self, attr, json_response[attr])
            else:
                raise ValueError(
                    f"Missing key {attr} in response from PowerWall. Either the PowerWall sent an invalid response or the API changed!")


class MetersResponse(Response):
    JSON_ATTRS = [
        "last_communication_time",
        "instant_power",
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


class SitemasterResponse(Response):
    JSON_ATTRS = [
        "status",
        "running",
        "connected_to_tesla"
    ]


class SiteinfoResponse(Response):
    JSON_ATTRS = [
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
    JSON_ATTRS = [
        "privacy_notice",
        "limited_warranty",
        "grid_services",
        "marketing",
        "registered",
        "timed_out_registration"
    ]
