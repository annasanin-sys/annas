import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

JIRA_HOST = os.getenv("JIRA_HOST").rstrip('/')
JIRA_EMAIL = os.getenv("JIRA_USER_EMAIL")
JIRA_TOKEN = os.getenv("JIRA_API_TOKEN")

def inspect_full_issue():
    issue_key = "AC-3644"
    print(f"--- Deep Inspection of {issue_key} ---")
    
    # 1. Fetch Issue with ALL fields and properties
    url = f"{JIRA_HOST}/rest/api/3/issue/{issue_key}?expand=names,renderedFields,schema,properties"
    
    try:
        resp = requests.get(url, headers={"Content-Type": "application/json"}, auth=(JIRA_EMAIL, JIRA_TOKEN))
        if resp.status_code != 200:
            print(f"Error: {resp.status_code}")
            return
            
        data = resp.json()
        
        # Check Custom Fields for 'Checklist'
        print("\n--- Custom Fields containing 'Checklist' ---")
        names = data.get('names', {})
        for field_id, field_name in names.items():
            if 'checklist' in field_name.lower():
                val = data['fields'].get(field_id)
                print(f"Field: {field_name} ({field_id})")
                print(f"Value: {val}")
                
        # Check Properties
        print("\n--- Issue Properties ---")
        properties = data.get('properties', {})
        print(f"Properties keys: {list(properties.keys())}")
        
        # Explicitly fetch checklist property if not expanded
        prop_url = f"{JIRA_HOST}/rest/api/3/issue/{issue_key}/properties/checklist"
        prop_resp = requests.get(prop_url, headers={"Content-Type": "application/json"}, auth=(JIRA_EMAIL, JIRA_TOKEN))
        if prop_resp.status_code == 200:
             print("\n--- Property 'checklist' content ---")
             print(json.dumps(prop_resp.json(), indent=2))
        else:
             print(f"\nProperty 'checklist' check: {prop_resp.status_code}")

    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    inspect_full_issue()
