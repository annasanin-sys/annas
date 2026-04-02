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

def inspect_issue(key):
    url = f"{JIRA_HOST}/rest/api/3/issue/{key}"
    try:
        resp = requests.get(url, headers=get_jira_headers(), auth=(JIRA_EMAIL, JIRA_TOKEN))
        resp.raise_for_status()
        data = resp.json()
        
        fields = data['fields']
        print(f"--- Issue {key} ---")
        print(f"Summary: {fields['summary']}")
        print(f"Type: {fields['issuetype']['name']}")
        print(f"Status: {fields['status']['name']}")
        print(f"Description (Raw): {json.dumps(fields.get('description'))}")
        # Check for attachments
        print(f"Attachments: {len(fields.get('attachment', []))}")
        for att in fields.get('attachment', []):
            print(f" - File: {att['filename']} (ID: {att['id']})")
            print(f"   URL: {att['content']}")
            print(f"   Mime: {att['mimeType']}")
        
    except Exception as e:
        print(f"Error fetching {key}: {e}")

if __name__ == "__main__":
    inspect_issue("AC-3315")
