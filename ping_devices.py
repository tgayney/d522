import subprocess
from devices_list import get_devices_list
import sys
from netmiko import ConnectHandler
import time



def verify_connectivity(fix=False):
    reachable_devices = []
    compromised_devices = []
    device_list = get_devices_list()
    if sys.platform == "win32":
        local_os_ping_option = "-n"
    elif sys.platform == "linux":
        local_os_ping_option = "-c"
    for device in device_list:
        if fix == True:
            if device["Device Name"] in ["DNS1", "DNS2"]:
                reachable_devices.append(device)
            

        else:
            if device["Device Address"] in ["None", "DHCP", "10.10.10.100"]:
                continue

            result = subprocess.run(
                    ["ping", local_os_ping_option, "4", device["Device Address"]],
                    capture_output=True,
                    text=True
                    )
            

            
            if result.returncode == 0:
                print(f"SUCCESS: {device["Device Name"]} is reachable")
                reachable_devices.append(device)
            else:
                print(f"ERROR: {device["Device Name"]} is not reachable")
                compromised_devices.append(device)
                continue
    return reachable_devices, compromised_devices

def verify_dns(fix=False):
    if fix == True:
        network_devices, _ = verify_connectivity(fix=True)
        
    else:    
        network_devices, compromised_devices = verify_connectivity()
    dns_servers = ["10.10.10.10", "10.10.10.20"]

    for device in network_devices:

        if "none" in [device["Username"], device["Password"]]:
            print("Couldn't find a valid user or pass")
            continue
        elif device["Device Name"] == "SMTP":
            continue
        elif device["OS"] == "Ubuntu": 
            Target = {
                "host": device["Device Address"],
                "device_type": "linux",
                "username": device["Username"],
                "password": device["Password"]
            }
        else:
            Target = {
                "host": device["Device Address"],
                "device_type": f"{device["OS"].lower()}",
                "username": device["Username"],
                "password": device["Password"]
            }


        with ConnectHandler(**Target) as connection:
            device["timestamp"] = time.localtime(time.time())
            if fix == True:
                if device["Device Address"] in dns_servers:
                    output = connection.send_command("sudo systemctl status resolved\n\n\n")
                    print(output)
                    output = connection.send_command("sudo systemctl restart resolved\n\n\n")
                    time.sleep(3)
                    output = connection.send_command("sudo systemctl status resolved\n\n\n")
                    print(output)

            elif Target["device_type"] == "vyos":
                output = connection.send_command("show dns forwarding statistics")
                print(f"{device["Device Name"]} is configured correctly")
            else:
                connection.send_command("sudo systemctl start systemd-resolved")
                output = connection.send_command("resolvectl status | grep 'DNS Servers'")
                extracted_dns = (
                    output.replace("DNS Servers:", "").replace("127.0.0.1", "")
                    .strip().split()
                )
                
                if sorted(dns_servers) == sorted(extracted_dns):
                    print(f"{device["Device Name"]} is configured correctly")
                elif device["Device Name"] in ["DNS1", "DNS2"]:
                    continue
                else:
                    device["description"] = f"Issue type: {device["Device Name"]}  \n\n\
                    Accepted DNS servers: {", ".join(dns_servers)}  \n\n\
                    Detected DNS servers: {", ".join(extracted_dns)}  \n\n\
                    Unexpected DNS servers: {", ".join(extracted_dns)} \n\n\
                    Missing accepted DNS servers: {", ".join(dns_servers)}"
                    print(device)
                    compromised_devices.append(device)
    if fix == True:
        return None
    return compromised_devices