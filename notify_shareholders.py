import smtplib
from ping_devices import verify_dns
import requests
import json


devices = verify_dns()


def notify_stakeholders():
    

    conn = smtplib.SMTP("smtp.d522.wgu.internal", 1025)
    conn.ehlo()
    conn.login("tgayne1@wgu.edu", "password")

    for device in devices:

        email_template_notification = f"""
        Subject: URGENT: Device Compromise Detected—Immediate Attention Required\n\n 

        Dear Stakeholders, 

        This is an automated alert to inform you that the following device(s) have been identified as compromised during the recent network scan: 

        Device Name: {device["Device Name"]} 
        IP Address: {device["Device Address"]} 
        Last Checked: {device["timestamp"]}

        Immediate investigation and remediation are recommended to prevent further impact. 

        If you have any questions or require additional information, please contact the IT support team. 

        Best regards,   
        Network Monitoring System
        """
        
        conn.sendmail(
            "tgayne1@wgu.edu", 
            "stakeholder@wgu.edu", 
            email_template_notification.replace("—", "-")
            )


def create_ticket():
    post_url = "http://helpdesk.d522.wgu.internal:5000/api/tickets"
    post_header = {
        "Authorization": "Bearer vGkbXkGLqQSo7YLflp9DutuG8st4xdPPF7wnTcwB0FE", 
        "Content-Type": "application/json"
        }
    for device in devices:

        ticket_data = {
            "assigned_to": "network-team",
            "description": f"{device["description"]}",  # Need to create an a new dictionary value in devices for this
            "priority": "high",
            "requester_email": "dns-monitor@d522.wgu.internal",
            "status": "open",
            "title": f"{device["Device Name"]} DNS Issue"
            }
        post_body = json.dumps(ticket_data)
        response = requests.post(post_url, data=post_body, headers=post_header)
        print(f"Response - Status Code: {response.status_code}")
    

notify_stakeholders()
create_ticket()

verify_dns(devices, fix=True)