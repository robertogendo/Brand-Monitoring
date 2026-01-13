# alerting.py
import requests
import json

TEAMS_WEBHOOK = "https://default19a4db07607d475fa5180e3b699ac7.d0.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/6ecb59c944374fa5af9796d20ac4b414/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=7gucKR3iGRiZaLYvxCMyWot3TsnHg_oJYWpGpqOy8rc"

def send_teams_alert(message):
    payload = {"text": message}
    response = requests.post(TEAMS_WEBHOOK, json=payload)
    if response.status_code != 200:
        print(f"Failed to send alert: {response.status_code}, {response.text}")
