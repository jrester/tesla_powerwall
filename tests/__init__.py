"""Tests for Tesla Powerwall API"""

ENDPOINT = "https://1.1.1.1/api/"

METERS_RESPONSE = {
    "site": {
        "last_communication_time": "2020-04-09T05:50:38.989687241-07:00",
        "instant_power": -5347.455078125,
        "instant_reactive_power": -664.1942901611328,
        "instant_apparent_power": 5388.546173843879,
        "frequency": 49.99971389770508,
        "energy_exported": 5512641.122754764,
        "energy_imported": 9852397.795532543,
        "instant_average_voltage": 232.0439249674479,
        "instant_total_current": 0,
        "i_a_current": 0,
        "i_b_current": 0,
        "i_c_current": 0,
        "timeout": 1500000000,
    },
    "battery": {
        "last_communication_time": "2020-04-09T05:50:38.990165237-07:00",
        "instant_power": -10,
        "instant_reactive_power": 600,
        "instant_apparent_power": 600.0833275470999,
        "frequency": 49.995000000000005,
        "energy_exported": 4379890,
        "energy_imported": 5265110,
        "instant_average_voltage": 230.8,
        "instant_total_current": -0.4,
        "i_a_current": 0,
        "i_b_current": 0,
        "i_c_current": 0,
        "timeout": 1500000000,
    },
    "load": {
        "last_communication_time": "2020-04-09T05:50:38.974944676-07:00",
        "instant_power": 734.1549565813606,
        "instant_reactive_power": -469.988307011022,
        "instant_apparent_power": 871.7066645380579,
        "frequency": 49.99971389770508,
        "energy_exported": 0,
        "energy_imported": 24751111.13611111,
        "instant_average_voltage": 232.0439249674479,
        "instant_total_current": 3.1638620001982423,
        "i_a_current": 0,
        "i_b_current": 0,
        "i_c_current": 0,
        "timeout": 1500000000,
    },
    "solar": {
        "last_communication_time": "2020-04-09T05:50:38.974944676-07:00",
        "instant_power": 6099.032958984375,
        "instant_reactive_power": -422.27491760253906,
        "instant_apparent_power": 6113.633873631454,
        "frequency": 49.95012283325195,
        "energy_exported": 21296639.987777833,
        "energy_imported": 65.52444450131091,
        "instant_average_voltage": 232.1537322998047,
        "instant_total_current": 0,
        "i_a_current": 0,
        "i_b_current": 0,
        "i_c_current": 0,
        "timeout": 1500000000,
    },
}

SITE_MASTER_RESPONSE = {
    "status": "StatusUp",
    "running": True,
    "connected_to_tesla": True,
    "power_supply_mode": False
}


STATUS_RESPONSE = {
    "start_time": "2020-10-28 20:14:11 +0800",
    "up_time_seconds": "17h11m31.214751424s",
    "is_new": False,
    "version": "1.50.1",
    "git_hash": "d0e69bde519634961cca04a616d2d4dae80b9f61",
    "commission_count": 0,
    "device_type": "hec",
    "sync_type": "v1"
}

GRID_STATUS_RESPONSE = {
    "grid_status": "SystemGridConnected",
    "grid_services_active": False
}

SITE_INFO_RESPONSE = {
    "max_system_energy_kWh": 0,
    "max_system_power_kW": 0,
    "site_name": "test",
    "timezone": "Europe/Berlin",
    "max_site_meter_power_kW": 1000000000,
    "min_site_meter_power_kW": -1000000000,
    "nominal_system_energy_kWh": 27,
    "nominal_system_power_kW": 10,
    "grid_code": {
        "grid_code": "test_grid_code",
        "grid_voltage_setting": 230,
        "grid_freq_setting": 50,
        "grid_phase_setting": "Single",
        "country": "Germany",
        "state": "*",
        "distributor": "*",
        "utility": "*",
        "retailer": "*",
        "region": "test_grid_code_region"
    }
}

POWERWALLS_RESPONSE = {
  "enumerating": False,
  "updating": False,
  "checking_if_offgrid": False,
  "running_phase_detection": False,
  "phase_detection_last_error": "phase detection not run",
  "bubble_shedding": False,
  "on_grid_check_error": "on grid check not run",
  "grid_qualifying": False,
  "grid_code_validating": False,
  "phase_detection_not_available": True,
  "powerwalls": [
    {
      "Type": "",
      "PackagePartNumber": "PartNumber1",
      "PackageSerialNumber": "SerialNumber1",
      "type": "acpw",
      "grid_state": "Grid_Uncompliant",
      "grid_reconnection_time_seconds": 0,
      "under_phase_detection": False,
      "updating": False,
      "commissioning_diagnostic": {
        "name": "Commissioning",
        "category": "InternalComms",
        "disruptive": False,
        "inputs": None,
        "checks": [
          {
            "name": "CAN connectivity",
            "status": "fail",
            "start_time": "2020-10-29T15:02:46.361506132+01:00",
            "end_time": "2020-10-29T15:02:46.361509132+01:00",
            "message": "Cannot perform this action with site controller running. From landing page, either \"STOP SYSTEM\" or \"RUN WIZARD\" to proceed.",
            "results": {},
            "debug": {}
          },
          {
            "name": "Enable switch",
            "status": "fail",
            "start_time": "2020-10-29T15:02:46.361511798+01:00",
            "end_time": "2020-10-29T15:02:46.361513798+01:00",
            "message": "Cannot perform this action with site controller running. From landing page, either \"STOP SYSTEM\" or \"RUN WIZARD\" to proceed.",
            "results": {},
            "debug": {}
          },
          {
            "name": "Internal communications",
            "status": "fail",
            "start_time": "2020-10-29T15:02:46.361516132+01:00",
            "end_time": "2020-10-29T15:02:46.361518132+01:00",
            "message": "Cannot perform this action with site controller running. From landing page, either \"STOP SYSTEM\" or \"RUN WIZARD\" to proceed.",
            "results": {},
            "debug": {}
          },
          {
            "name": "Firmware up-to-date",
            "status": "fail",
            "start_time": "2020-10-29T15:02:46.361520132+01:00",
            "end_time": "2020-10-29T15:02:46.361522132+01:00",
            "message": "Cannot perform this action with site controller running. From landing page, either \"STOP SYSTEM\" or \"RUN WIZARD\" to proceed.",
            "results": {},
            "debug": {}
          }
        ]
      },
      "update_diagnostic": {
        "name": "Firmware Update",
        "category": "InternalComms",
        "disruptive": True,
        "inputs": None,
        "checks": [
          {
            "name": "Powerwall firmware",
            "status": "not_run",
            "start_time": None,
            "end_time": None,
            "progress": 0,
            "results": None,
            "debug": None
          },
          {
            "name": "Battery firmware",
            "status": "not_run",
            "start_time": None,
            "end_time": None,
            "progress": 0,
            "results": None,
            "debug": None
          },
          {
            "name": "Inverter firmware",
            "status": "not_run",
            "start_time": None,
            "end_time": None,
            "progress": 0,
            "results": None,
            "debug": None
          },
          {
            "name": "Grid code",
            "status": "not_run",
            "start_time": None,
            "end_time": None,
            "progress": 0,
            "results": None,
            "debug": None
          }
        ]
      },
      "bc_type": None
    },
    {
      "Type": "",
      "PackagePartNumber": "PartNumber2",
      "PackageSerialNumber": "SerialNumber2",
      "type": "acpw",
      "grid_state": "Grid_Uncompliant",
      "grid_reconnection_time_seconds": 0,
      "under_phase_detection": False,
      "updating": False,
      "commissioning_diagnostic": {
        "name": "Commissioning",
        "category": "InternalComms",
        "disruptive": False,
        "inputs": None,
        "checks": [
          {
            "name": "CAN connectivity",
            "status": "fail",
            "start_time": "2020-10-29T15:02:46.361754463+01:00",
            "end_time": "2020-10-29T15:02:46.361757797+01:00",
            "message": "Cannot perform this action with site controller running. From landing page, either \"STOP SYSTEM\" or \"RUN WIZARD\" to proceed.",
            "results": {},
            "debug": {}
          },
          {
            "name": "Enable switch",
            "status": "fail",
            "start_time": "2020-10-29T15:02:46.36176013+01:00",
            "end_time": "2020-10-29T15:02:46.36176213+01:00",
            "message": "Cannot perform this action with site controller running. From landing page, either \"STOP SYSTEM\" or \"RUN WIZARD\" to proceed.",
            "results": {},
            "debug": {}
          },
          {
            "name": "Internal communications",
            "status": "fail",
            "start_time": "2020-10-29T15:02:46.36176413+01:00",
            "end_time": "2020-10-29T15:02:46.36176713+01:00",
            "message": "Cannot perform this action with site controller running. From landing page, either \"STOP SYSTEM\" or \"RUN WIZARD\" to proceed.",
            "results": {},
            "debug": {}
          },
          {
            "name": "Firmware up-to-date",
            "status": "fail",
            "start_time": "2020-10-29T15:02:46.361769463+01:00",
            "end_time": "2020-10-29T15:02:46.361771463+01:00",
            "message": "Cannot perform this action with site controller running. From landing page, either \"STOP SYSTEM\" or \"RUN WIZARD\" to proceed.",
            "results": {},
            "debug": {}
          }
        ]
      },
      "update_diagnostic": {
        "name": "Firmware Update",
        "category": "InternalComms",
        "disruptive": True,
        "inputs": None,
        "checks": [
          {
            "name": "Powerwall firmware",
            "status": "not_run",
            "start_time": None,
            "end_time": None,
            "progress": 0,
            "results": None,
            "debug": None
          },
          {
            "name": "Battery firmware",
            "status": "not_run",
            "start_time": None,
            "end_time": None,
            "progress": 0,
            "results": None,
            "debug": None
          },
          {
            "name": "Inverter firmware",
            "status": "not_run",
            "start_time": None,
            "end_time": None,
            "progress": 0,
            "results": None,
            "debug": None
          },
          {
            "name": "Grid code",
            "status": "not_run",
            "start_time": None,
            "end_time": None,
            "progress": 0,
            "results": None,
            "debug": None
          }
        ]
      },
      "bc_type": None
    }
  ],
  "has_sync": False,
  "sync": None,
  "states": []
}

OPERATION_RESPONSE = {
  
}