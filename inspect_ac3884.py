import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

JIRA_HOST = os.getenv("JIRA_HOST").rstrip('/')
JIRA_EMAIL = os.getenv("JIRA_USER_EMAIL")
JIRA_TOKEN = os.getenv("JIRA_API_TOKEN")

def inspect_ac3884():
    issue_key = "AC-3884"
    print(f"--- Inspecting {issue_key} ---")
    url = f"{JIRA_HOST}/rest/api/3/issue/{issue_key}"
    
    try:
        resp = requests.get(url, headers={"Content-Type": "application/json"}, auth=(JIRA_EMAIL, JIRA_TOKEN))
        if resp.status_code != 200:
            print(f"Error fetching issue: {resp.status_code} - {resp.text}")
            return
            
        data = resp.json()
        fields = data['fields']
        print(f"Summary: {fields['summary']}")
        print(f"Status: {fields['status']['name']}")
        print(f"Issue Type: {fields['issuetype']['name']} (Subtask: {fields['issuetype']['subtask']})")
        
        parent = fields.get('parent')
        if parent:
            print(f"Parent: {parent['key']} - {parent['fields']['summary']}")
        else:
            print("Parent: NONE")

        # Check properties for checklist
        print("\nChecking Checklist Property...")
        prop_url = f"{JIRA_HOST}/rest/api/3/issue/{issue_key}/properties/checklist"
        prop_resp = requests.get(prop_url, headers={"Content-Type": "application/json"}, auth=(JIRA_EMAIL, JIRA_TOKEN))
        if prop_resp.status_code == 200:
            print(json.dumps(prop_resp.json(), indent=2))
        else:
             print(f"Checklist property not found or error: {prop_resp.status_code}")

    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    inspect_ac3884()
