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

def list_property_keys():
    # https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-properties/#api-rest-api-3-issue-issueidorkey-properties-get
    url = f"{JIRA_HOST}/rest/api/3/issue/{TARGET_ISSUE}/properties"
    print(f"Listing properties for {TARGET_ISSUE}...")
    try:
        resp = requests.get(url, headers=get_jira_headers(), auth=get_jira_auth())
        resp.raise_for_status()
        data = resp.json()
        
        # Response is list of {key: "...", self: "..."}
        keys = data.get('keys', [])
        print(f"Found {len(keys)} properties.")
        for k in keys:
            print(f"  - {k['key']}")
            
            # Fetch content for each
            prop_url = k['self']
            r = requests.get(prop_url, headers=get_jira_headers(), auth=get_jira_auth())
            if r.status_code == 200:
                print(f"     Content: {r.text[:200]}...")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_property_keys()
