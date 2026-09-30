import subprocess
from devices_list import get_devices_list
import sys
from netmiko import ConnectHandler
import time
from datetime import datetime


def update_log(name):
    logfile = open("log.txt", "a")
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logfile.write(f"{name}'s DNS service is functioning correctly and is stable at {time}\n")
    logfile.close()


def verify_connectivity():
    reachable_devices = []
    compromised_devices = []
    device_list = get_devices_list()
    if sys.platform == "win32":  # Run windows cmd
        local_os_ping_option = "-n"
    elif sys.platform == "linux":  # Run linux cmd
        local_os_ping_option = "-c"
    
    for device in device_list:
        # Check ping status (4 times due to ARP) and DNS settings
        if device["Device Address"] in ["None", "DHCP", "10.10.10.100"]:
            continue

        result = subprocess.run(
            ["ping", local_os_ping_option, "4", device["Device Address"]],
            capture_output=True,
            text=True
        )
            

            
        if result.returncode == 0:  # Ping success
            print(f"SUCCESS: {device["Device Name"]} is reachable")
            device["Reachability"] = True
            device["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            reachable_devices.append(device)
            
        else:  # Ping failure
            print(f"ERROR: {device["Device Name"]} is not reachable")
            device["Reachability"] = False
            device["description"] = f"Issue type: \
                {device["Device Name"]} is unreachable"
            device["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            device["DNS Issue"] = False
            compromised_devices.append(device)
            continue
    print("\n\n")
    return reachable_devices, compromised_devices

def verify_dns(fix_devices=None, fix=False):  # Check DNS
    if fix == True:
        network_devices = fix_devices
        
    
        
    else:    
        network_devices, compromised_devices = verify_connectivity()

    dns_servers = ["10.10.10.10", "10.10.10.20"]
    loopback_dns = ["127.0.0.53"]

    for device in network_devices:
        if device["Reachability"] == False:
            continue

        elif "none" in [device["Username"], device["Password"]]:
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
            if fix != True:
                device["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if fix == True:
                if device["Device Address"] in dns_servers:
                    if device.get("state active") != True:
                        print(f"\n\n\nRestarting DNS service for {device["Device Name"]}")
                        output = connection.send_command(
                            "sudo systemctl restart named"
                        )
                        time.sleep(3)
                        output = connection.send_command(
                            "systemctl status --no-pager named"
                        )
                        print(output + "\n\n")
                        update_log(device["Device Name"])
                    
                    
                
                else:  # Fixing devices with bad DNS settings
                
                    print(f"\n\n\n\nFixing Server: {device["Device Name"]}\n\n\n")
                    print(f"Current DNS Settings: {device["Current DNS Setting"]}\n")
                    connection.send_command(
                    f'echo -e "nameserver {dns_servers[0]}\\nnameserver {dns_servers[1]}" | \
                    sudo tee /etc/resolv.conf > /dev/null', read_timeout=60
                    )
                    connection.send_command("sudo systemctl enable systemd-resolved --now")
                    time.sleep(10)
                    output = connection.send_command(
                        "cat /etc/resolv.conf | grep 'nameserver' | awk '{print $2}'"
                    )
                    device["Current DNS Setting"] = output.split()
                    update_log(device["Device Name"])
                    print(f"Updated DNS Settings: {output}\n")

            elif Target["device_type"] == "vyos":
                output = connection.send_command("show dns forwarding statistics")
                print(f"{device["Device Name"]} is configured correctly")
                update_log(device["Device Name"])
            elif device["Device Address"] in dns_servers:
                output = connection.send_command(
                    "systemctl --no-pager status named"
                )
                print(output + "\n\n")
                output = connection.send_command(
                    "systemctl --no-pager status named | grep 'Active' | awk '{print $2 $3}'"
                )
                output = output.replace("Active:", "").lstrip().rstrip()
                print(f"\n\n\n{output}\n\n\n")
                if output != "active(running)":  # Create ticket if DNS named down
                    device["description"] = f"Issue type: {device["Device Name"]}  \n\n\
                    Accepted DNS service state: active(running)  \n\n\
                    Detected DNS servers state: {output}"
                    device["state active"] = False
                    device["DNS Issue"] = False
                    compromised_devices.append(device)
                else:
                    update_log(device["Device Name"])
                    continue
            else:
                
                output = connection.send_command("cat /etc/resolv.conf | grep 'nameserver' | awk '{print $2}'")
                extracted_dns = output.split()
                
                    
                
                if sorted(extracted_dns) == sorted(dns_servers):
                    print(f"{device["Device Name"]} is configured correctly")

                elif sorted(extracted_dns) == sorted(loopback_dns):
                    print(f"{device["Device Name"]} is configured correctly")
                    
                else:
                    device["Current DNS Setting"] = extracted_dns
                    device["DNS Issue"] = True
                    device["description"] = f"Issue type: {device["Device Name"]}  \n\n\
                    Accepted DNS servers: {", ".join(dns_servers)}  \n\n\
                    Detected DNS servers: {", ".join(extracted_dns)}  \n\n\
                    Unexpected DNS servers: {", ".join(extracted_dns)} \n\n\
                    Missing accepted DNS servers: {", ".join(dns_servers)}"
                    
                    compromised_devices.append(device)
    if fix == True:
        return network_devices
    print(compromised_devices)
    return compromised_devices