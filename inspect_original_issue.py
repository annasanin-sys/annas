import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

JIRA_HOST = os.getenv("JIRA_HOST").rstrip('/')
JIRA_EMAIL = os.getenv("JIRA_USER_EMAIL")
JIRA_TOKEN = os.getenv("JIRA_API_TOKEN")
TARGET_ISSUE = "AC-3286" # The original issue

CHECKLIST_FIELDS = [
    "customfield_10040", 
    "customfield_10041",
    "customfield_10034", 
    "customfield_10035",
]

def get_jira_auth():
    return (JIRA_EMAIL, JIRA_TOKEN)

def get_jira_headers():
    return {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

def inspect_original_issue():
    fields_param = ",".join(CHECKLIST_FIELDS)
    url = f"{JIRA_HOST}/rest/api/3/issue/{TARGET_ISSUE}?fields={fields_param},summary"
    
    print(f"Fetching Original Issue {TARGET_ISSUE}...")
    try:
        resp = requests.get(url, headers=get_jira_headers(), auth=get_jira_auth())
        resp.raise_for_status()
        data = resp.json()
        
        fields = data.get('fields', {})
        print(f"Summary: {fields.get('summary')}")
        
        found = False
        for f in CHECKLIST_FIELDS:
            val = fields.get(f)
            if val:
                print(f"FOUND {f}: {json.dumps(val, indent=2)}")
                found = True
            else:
                print(f"{f}: None")
                
        if not found:
            print("No checklist data found in original issue either.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_original_issue()
