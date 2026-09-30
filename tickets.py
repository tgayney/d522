import requests
import json




get_url = "http://helpdesk.d522.wgu.internal:5000/api/tickets"
post_header = {
    "Authorization": "Bearer vGkbXkGLqQSo7YLflp9DutuG8st4xdPPF7wnTcwB0FE", 
    "Content-Type": "application/json"
    }

def clear_tickets():
    response = requests.get(get_url, headers=post_header)
    response_dict = response.json()
    for ticket in response_dict:
        delete_url = f"{get_url}/{ticket['id']}"
        response = requests.delete(delete_url, headers=post_header)
        print(f"Response - Status Code: {response.status_code}")
clear_tickets()