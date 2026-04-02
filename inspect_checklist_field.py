import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

JIRA_HOST = os.getenv("JIRA_HOST").rstrip('/')
JIRA_EMAIL = os.getenv("JIRA_USER_EMAIL")
JIRA_TOKEN = os.getenv("JIRA_API_TOKEN")
TARGET_ISSUE = "AC-3309"

# Candidate fields from previous exploration
CHECKLIST_FIELDS = [
    "customfield_10040", # Checklist Template
    "customfield_10041", # Checklist Text (view-only)
    "customfield_10034", # Checklist Progress
    "customfield_10035", # Checklist Progress %
]

def get_jira_auth():
    return (JIRA_EMAIL, JIRA_TOKEN)

def get_jira_headers():
    return {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

def inspect_checklist_fields():
    # Fetch specific fields
    fields_param = ",".join(CHECKLIST_FIELDS)
    url = f"{JIRA_HOST}/rest/api/3/issue/{TARGET_ISSUE}?fields={fields_param},summary,description"
    
    print(f"Fetching {TARGET_ISSUE} with fields: {fields_param}...")
    try:
        resp = requests.get(url, headers=get_jira_headers(), auth=get_jira_auth())
        resp.raise_for_status()
        data = resp.json()
        
        fields = data.get('fields', {})
        print("\n--- Field Values ---")
        for f in CHECKLIST_FIELDS:
            val = fields.get(f)
            print(f"{f}: {json.dumps(val, indent=2) if val else 'None'}")
            
        print("\n--- Summary ---")
        print(fields.get('summary'))
        
        print("\n--- Description ---")
        print(fields.get('description'))

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_checklist_fields()
