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

def inspect_meta():
    url = f"{JIRA_HOST}/rest/api/3/issue/{TARGET_ISSUE}?expand=editmeta,names"
    print(f"Fetching {TARGET_ISSUE} metadata...")
    try:
        resp = requests.get(url, headers=get_jira_headers(), auth=get_jira_auth())
        resp.raise_for_status()
        data = resp.json()
        
        editmeta = data.get('editmeta', {}).get('fields', {})
        names = data.get('names', {})
        
        print(f"Found {len(editmeta)} editable fields.")
        
        candidates = []
        for key, field_meta in editmeta.items():
            name = field_meta.get('name', names.get(key, key))
            # Check for "check" or "smart" or "railsware" or "hero"
            if "check" in name.lower() or "customfield" in key:
                 candidates.append((key, name, field_meta.get('schema', {}).get('type')))
                 
        for k, n, t in candidates:
            print(f"Field: {n} ({k}) Type: {t}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_meta()
