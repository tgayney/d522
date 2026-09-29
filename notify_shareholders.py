import smtplib
from ping_devices import verify_dns
import requests
import json
from dns_backup import backup


devices = verify_dns()
print(devices)
Expected_DNS_Setting = ["10.10.10.10", "10.10.10.20"]

def notify_stakeholders():
    

    conn = smtplib.SMTP("smtp.d522.wgu.internal", 1025)
    conn.ehlo()
    conn.login("tgayne1@wgu.edu", "password")
    
    
    for device in devices:
        print(f"Running notify stakeholder: {device}")
        if device["Reachability"] == False:
            email_template_notification = f"""
            Subject: Network Device Unavailable: {device["Device Name"]} ({device["Device Address"]})\n\n 

            Dear Network Administrator, 

            

            This is an automated notification that the following network device is currently unavailable: 

            

            Device Name: {device["Device Name"]} 
            IP Address: {device["Device Address"]} 
            Last Checked: {device["timestamp"]}

            

            Please investigate this issue at your earliest convenience. 

            

            Best regards,   

            Network Monitoring System 
            """

        elif sorted(device["Current DNS Setting"]) != sorted(Expected_DNS_Setting):
            email_template_notification = f"""
            Subject: DNS Configuration Alert: {device["Device Name"]} ({device["Device Address"]})\n\n 

            Dear Network Administrator, 

            

            This is an automated alert that the DNS configuration for the following device has been altered from the expected settings: 

            

            Device Name: {device["Device Name"]} 

            IP Address: {device["Device Address"]} 

            Detected DNS Setting: {device["Current DNS Setting"]} 

            Expected DNS Setting: {" ".join(Expected_DNS_Setting)} 

            Time Detected: {device["timestamp"]} 

            

            The system will attempt to automatically correct this configuration. 

            

            Best regards,   

            Network Monitoring System  
            """

        else:
            continue

        
        conn.sendmail(
            "tgayne1@wgu.edu", 
            "stakeholder@wgu.edu", 
            email_template_notification.replace("—", "-")
            )



def ticket():
    post_url = "http://helpdesk.d522.wgu.internal:5000/api/tickets"
    ticket_header = {
        "Authorization": "Bearer vGkbXkGLqQSo7YLflp9DutuG8st4xdPPF7wnTcwB0FE", 
        "Content-Type": "application/json"
        }
    for device in devices:
        print(f"this is the device running: {device}")

        if device["Reachability"] == False:
            ticket_data = {
                "assigned_to": "network-team",
                "description": f"{device["description"]}",
                "priority": "high",
                "requester_email": "dns-monitor@d522.wgu.internal",
                "status": "open",
                "title": f"{device["Device Name"]} Ping Issue"
                }
            post_body = json.dumps(ticket_data)
            response = requests.post(
                post_url, 
                data=post_body, 
                headers=ticket_header)
            print(f"Response - Status Code: {response.status_code}")
            response_dict = response.json()
            device["ticket id"] = response_dict["id"]
        
        elif device["Device Address"] in Expected_DNS_Setting:
            continue

        elif sorted(device["Current DNS Setting"]) != \
            sorted(Expected_DNS_Setting):
            ticket_data = {
                "assigned_to": "network-team",
                "description": f"{device["description"]}",
                "priority": "high",
                "requester_email": "dns-monitor@d522.wgu.internal",
                "status": "open",
                "title": f"{device["Device Name"]} DNS Issue"
                }
            post_body = json.dumps(ticket_data)
            response = requests.post(
                post_url, 
                data=post_body, 
                headers=ticket_header)
            print(f"Response - Status Code: {response.status_code}")
            response_dict = response.json()
            device["ticket id"] = response_dict["id"]

        elif sorted(device["Current DNS Setting"]) == \
            sorted(Expected_DNS_Setting):
            print(f"Running PATCH PORTION OF CODE FOR: {device}")
            patch_url = f"{post_url}/{device["ticket id"]}"
            ticket_data = {
                "status": "resolved",
                }
            patch_body = json.dumps(ticket_data)
            response = requests.patch(
                patch_url, 
                data=patch_body, 
                headers=ticket_header)
            print(f"Response - Status Code: {response.status_code}")
            
    

def send_Resolution():
    device_list = []
    conn = smtplib.SMTP("smtp.d522.wgu.internal", 1025)
    conn.ehlo()
    conn.login("tgayne1@wgu.edu", "password")

    for resolution in devices:
        device_list.append(f"{resolution["Device Name"]}:{resolution["Device Address"]}")
        
        if resolution["DNS Issue"] == True:
            email_template_notification = f"""
                Subject: DNS Configuration Corrected: {resolution["Device Name"]} ({resolution["IP Address"]})
                Dear Network Administrator, 

                The DNS configuration issue previously detected on the following device has been automatically corrected: 

                Device Name: {resolution["Device Name"]} 

                IP Address: {resolution["Device Address"]} 

                Corrected DNS Setting: {resolution["Current DNS Setting"]} 

                Time Detected: {resolution["timestamp"]} 

                        

                No further action is required at this time. 

                        

                Best regards,   

                Network Monitoring System 
                """
            conn.sendmail(
                        "tgayne1@wgu.edu", 
                        "stakeholder@wgu.edu", 
                        email_template_notification.replace("—", "-")
                        )
    device_list = ", ".join(device_list)

    resolution_Notification_Email = f"""
    Dear Stakeholders, 

    

    This is an automated notification to inform you that the DNS service issue and all related device compromises have been successfully resolved. The following devices were affected and have now been remediated: 

    

    {device_list} 

    

    No further action is required at this time. If you have any questions or concerns, please contact the IT support team. 

    

    Thank you for your attention. 

    

    Best regards,   

    Network Monitoring System
    """

    conn.sendmail(
                "tgayne1@wgu.edu", 
                "stakeholder@wgu.edu", 
                resolution_Notification_Email.replace("—", "-")
                )

backup()
notify_stakeholders()
ticket()
verify_dns(devices, fix=True)
send_Resolution()
ticket()