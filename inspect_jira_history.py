import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

JIRA_HOST = os.getenv("JIRA_HOST").rstrip('/')
JIRA_EMAIL = os.getenv("JIRA_USER_EMAIL")
JIRA_TOKEN = os.getenv("JIRA_API_TOKEN")

def get_jira_headers():
    return {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

def inspect_history(issue_key):
    print(f"--- Inspecting History for {issue_key} ---")
    # improved endpoint to get changelog
    url = f"{JIRA_HOST}/rest/api/3/issue/{issue_key}/changelog"
    
    try:
        resp = requests.get(url, headers=get_jira_headers(), auth=(JIRA_EMAIL, JIRA_TOKEN))
        if resp.status_code != 200:
            print(f"Error fetching changelog: {resp.status_code} - {resp.text}")
            return
            
        data = resp.json()
        values = data.get('values', [])
        print(f"Found {len(values)} history entries.")
        
        # Look for subtask related changes
        for entry in values:
            created = entry.get('created')
            author = entry.get('author', {}).get('displayName', 'Unknown')
            items = entry.get('items', [])
            
            for item in items:
                field = item.get('field')
                if field in ['subtasks', 'Link', 'IssueParentAssociation']: # Common fields for subtask linking
                    print(f"\nTime: {created} | Author: {author}")
                    print(f"  Field: {field}")
                    print(f"  From: {item.get('fromString')} (id: {item.get('from')})")
                    print(f"  To:   {item.get('toString')} (id: {item.get('to')})")

    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    inspect_history("AC-3653")
