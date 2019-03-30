class Response:
    JSON_ATTRS = ["last_communication_time", "instant_power", "instant_reactive_power", "instant_apparent_power", "frequency", "energy_exported", "energy_imported", "instant_average_voltage", "instant_total_current", "i_a_current", "i_b_current", "i_c_current"]

    def __init__(self, response_json):
        self.response_json = response_json

        for attr in Response.JSON_ATTRS:
            setattr(self, attr, response_json[attr])