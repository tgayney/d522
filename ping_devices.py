import subprocess
from devices_list import get_devices_list
import sys
from netmiko import ConnectHandler
import time
from datetime import datetime



def verify_connectivity(fix=False):
    reachable_devices = []
    compromised_devices = []
    device_list = get_devices_list()
    if sys.platform == "win32":  # Run windows cmd
        local_os_ping_option = "-n"
    elif sys.platform == "linux":  # Run linux cmd
        local_os_ping_option = "-c"
    print(f"\n\nOG device list {device_list}")
    for device in device_list:
        if fix == True:  # Troubleshoot and fix devices that have been determined to be faulty
            if device["Device Name"] in ["DNS1", "DNS2"]:
                reachable_devices.append(device)
            

        else:  # Check ping status (4 times due to ARP) and DNS settings
            if device["Device Address"] in ["None", "DHCP", "10.10.10.100"]:
                continue

            result = subprocess.run(
                    ["ping", local_os_ping_option, "4", device["Device Address"]],
                    capture_output=True,
                    text=True
                    )
            

            
            if result.returncode == 0:  # Ping success
                print(f"SUCCESS: {device["Device Name"]} is reachable")
                reachable_devices.append(device)
            else:  # Ping failure
                print(f"ERROR: {device["Device Name"]} is not reachable")
                compromised_devices.append(device)
                continue
    print("\n\n")
    return reachable_devices, compromised_devices

def verify_dns(fix_devices=None, fix=False):  # Check DNS
    if fix == True:
        network_devices, _ = verify_connectivity(fix=True)
        print(f"\n\n\n\n NETWORK DEVICES \n\n\n\n {network_devices}")
    
        
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
            device["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if fix == True:
                if device["Device Name"] in dns_servers:
                    if device["state active"] != True:
                        output = connection.send_command(
                            "sudo systemctl restart named"
                        )
                        time.sleep(3)
                        output = connection.send_command(
                            "systemctl status --no-pager named"
                        )
                        
                        print(output + "\n\n")
                    
                
                else:
                    for d in fix_devices:  # Fixing devices with bad DNS settings
                        print(device["Device Name"])
                        print(d["Device Name"])
                        is_match = device["Device Name"] == d["Device Name"]
                        is_match2 = device.get("Device Name") == d.get("Device Name")
                        print(f"check 1 {is_match}, check 2 {is_match2}")
                        if device["Device Name"] == d["Device Name"]:
                            print("\n\n\n\nthisisrunning\n\n\n")
                            output = connection.send_command(
                                "cat /etc/resolv.conf"
                            )
                            print(f"Current DNS Settings: {output}\n")
                            output = connection.send_command(
                            f"echo -e \"nameserver {dns_servers[0]}\nnameserver {dns_servers[1]}\" | \
                            sudo tee /etc/resolv.conf > /dev/null"
                            )
                            print(f"Updated DNS Settings: {output}\n")

            elif Target["device_type"] == "vyos":
                output = connection.send_command("show dns forwarding statistics")
                print(f"{device["Device Name"]} is configured correctly")
            elif device["Device Address"] in dns_servers:
                output = connection.send_command(
                    "systemctl --no-pager status named"
                )
                print(output + "\n\n")
                output = connection.send_command(
                    "systemctl --no-pager status named | grep 'Active'"
                )
                output = output.replace("Active:", "").lstrip().rstrip()
                if output != "active (running)":  # Create ticket if DNS named down
                    device["description"] = f"Issue type: {device["Device Name"]}  \n\n\
                    Accepted DNS service state: active (running)  \n\n\
                    Detected DNS servers state: {", ".join(output)}"
                    device["state active"] = False
                    compromised_devices.append(device)
                else:
                    continue
            else:
                
                output = connection.send_command("resolvectl status | grep 'DNS Servers'")
                extracted_dns = (
                    output.replace("DNS Servers:", "").replace("127.0.0.1", "")
                    .strip().split()
                )
                
                if sorted(dns_servers) == sorted(extracted_dns):
                    print(f"{device["Device Name"]} is configured correctly")
                
                    
                else:
                    device["description"] = f"Issue type: {device["Device Name"]}  \n\n\
                    Accepted DNS servers: {", ".join(dns_servers)}  \n\n\
                    Detected DNS servers: {", ".join(extracted_dns)}  \n\n\
                    Unexpected DNS servers: {", ".join(extracted_dns)} \n\n\
                    Missing accepted DNS servers: {", ".join(dns_servers)}"
                    
                    compromised_devices.append(device)
    if fix == True:
        return None
    return compromised_devices