import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

JIRA_HOST = os.getenv("JIRA_HOST").rstrip('/')
JIRA_EMAIL = os.getenv("JIRA_USER_EMAIL")
JIRA_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_PROJECT = os.getenv("JIRA_PROJECT_KEY")

def get_jira_headers():
    return {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

def inspect_subtasks():
    url = f"{JIRA_HOST}/rest/api/3/search/jql"
    # Fetch all, then filter
    payload = {
        "jql": f"project = {JIRA_PROJECT}",
        "fields": ["summary", "status", "issuetype", "parent"],
        "maxResults": 200
    }
    
    try:
        resp = requests.post(url, json=payload, headers=get_jira_headers(), auth=(JIRA_EMAIL, JIRA_TOKEN))
        resp.raise_for_status()
        all_issues = resp.json().get("issues", [])
        
        issues = [i for i in all_issues if i['fields']['issuetype']['subtask']]
        
        statuses = set(i['fields']['status']['name'] for i in issues)
        print(f"Found {len(issues)} subtasks.")
        print(f"Unique Statuses found: {statuses}")
        
        print("Inspecting first 5:")
        for i in issues[:5]:
            print("-" * 30)
            print(f"Key: {i['key']}")
            print(f"Summary: '{i['fields']['summary']}'")
            print(f"Status: '{i['fields']['status']['name']}'")
            parent = i['fields'].get('parent')
            if parent:
                print(f"Parent: {parent['key']} - '{parent['fields']['summary']}'")
            else:
                print("Parent: None")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_subtasks()
