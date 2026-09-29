import requests
import json

post_url = "http://helpdesk.d522.wgu.internal:5000/api/tickets/1"
post_header = {
    "Authorization": "Bearer vGkbXkGLqQSo7YLflp9DutuG8st4xdPPF7wnTcwB0FE", 
    "Content-Type": "application/json"
    }
x= 1
if x == 2:
    ticket_data = {
        "assigned_to": "network-team",
        "description": "description of the issue",
        "priority": "high",
        "requester_email": "dns-monitor@d522.wgu.internal",
        "status": "open",
        "title": "Issue"
        }
else:
    ticket_data = {
        "status": "resolved"
    }
post_body = json.dumps(ticket_data)
response = requests.patch(post_url, data=post_body, headers=post_header)
print(f"Response - Status Code: {response.json()}")
response_dict = response.json()
print(response_dict["id"])