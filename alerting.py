# alerting.py
import requests
import json

TEAMS_WEBHOOK = "https://example.com"

def send_teams_alert(message):
    payload = {"text": message}
    response = requests.post(TEAMS_WEBHOOK, json=payload)
    if response.status_code != 200:
        print(f"Failed to send alert: {response.status_code}, {response.text}")
