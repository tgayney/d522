from devices_list import get_devices_list 
import re
from pathlib import Path
import os
from netmiko import ConnectHandler 


def backup():
    devices = get_devices_list()
    pwd = Path.cwd()
    pwd = (f"{pwd}/DNS-Backup")
    for device in devices:
        is_dns = re.search(r"DNS(\d+)", device.get("Device Name"))
        if is_dns:
            dns_number = is_dns.group(1)
            backup_dir = f"{pwd}/server-{dns_number}"
            os.makedirs(backup_dir, exist_ok=True)
            backup_file_path = Path(f"{backup_dir}/record-config.txt")
            backup_file = open(backup_file_path, "w")
            Target = {
                            "host": device["Device Address"],
                            "device_type": "linux",
                            "username": device["Username"],
                            "password": device["Password"]
                        }
            with ConnectHandler(**Target) as connection:
                backup = connection.send_command(f"cat /etc/bind/named.conf")
            backup_file.write(f"{backup}")
            backup_file.close()
