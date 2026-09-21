"""
This script obtains a list which it's items include dictionary key value pairs
correspond to devices from devices.csv
"""


from pathlib import Path
import csv


def get_devices_list() -> list:
    device_list = []  # Constant to append rows from devices csv to this list.
    device_name_list = []  # For requested screenshot
    with open(Path("network_devices.csv"), "r") as file:
        device_rows = csv.DictReader(file)

        for row in device_rows:
            device_list.append(row)

        for device in device_list:
            device_name_list.append(device["Device Name"])
    print(device_name_list)
    return device_list