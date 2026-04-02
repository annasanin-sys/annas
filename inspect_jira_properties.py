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

def inspect_properties():
    # properties=*all*
    url = f"{JIRA_HOST}/rest/api/3/issue/{TARGET_ISSUE}?properties=*all*"
    print(f"Fetching properties for {TARGET_ISSUE}...")
    try:
        resp = requests.get(url, headers=get_jira_headers(), auth=get_jira_auth())
        resp.raise_for_status()
        data = resp.json()
        
        props = data.get('properties', {})
        print(f"Properties found: {json.dumps(props, indent=2)}")
        
        # If any property looks promising, fetch it
        for key, val in props.items():
             # properties in the issue response might just be a dict if expanded, 
             # but usually they are just keys if we need to fetch them individually?
             # Jira v3 with ?properties=*all* usually returns the actual properties dict
             pass

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_properties()
