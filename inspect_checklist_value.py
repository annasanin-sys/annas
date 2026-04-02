import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

JIRA_HOST = os.getenv("JIRA_HOST").rstrip('/')
JIRA_EMAIL = os.getenv("JIRA_USER_EMAIL")
JIRA_TOKEN = os.getenv("JIRA_API_TOKEN")
TARGET_ISSUE = "AC-3309"

def get_jira_auth():
    return (JIRA_EMAIL, JIRA_TOKEN)

def get_jira_headers():
    return {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

def inspect_value():
    url = f"{JIRA_HOST}/rest/api/3/issue/{TARGET_ISSUE}/properties/checklist"
    try:
        resp = requests.get(url, headers=get_jira_headers(), auth=get_jira_auth())
        if resp.status_code == 200:
            data = resp.json()
            val = data.get('value', {})
            items_str = val.get('items', '')
            print(f"Raw Items String: {repr(items_str)}")
            print(json.dumps(val, indent=2))
        else:
            print(f"Property not found: {resp.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_value()
