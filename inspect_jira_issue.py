import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

JIRA_HOST = os.getenv("JIRA_HOST").rstrip('/')
JIRA_EMAIL = os.getenv("JIRA_USER_EMAIL")
JIRA_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_PROJECT = os.getenv("JIRA_PROJECT_KEY")

def get_jira_auth():
    return (JIRA_EMAIL, JIRA_TOKEN)

def get_jira_headers():
    return {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

def inspect_issue():
    # 1. Fetch one issue to see structure
    search_url = f"{JIRA_HOST}/rest/api/3/search/jql"
    payload = {
        "jql": f"project = {JIRA_PROJECT}",
        "fields": ["summary", "status", "issuetype", "description"],
        "maxResults": 1
    }
    
    try:
        print("Fetching a Jira issue...")
        resp = requests.post(search_url, json=payload, headers=get_jira_headers(), auth=get_jira_auth())
        if resp.status_code != 200:
            print(f"Error fetching issues: {resp.status_code} {resp.text}")
            return

        issues = resp.json().get("issues", [])
        if not issues:
            print("No issues found in project.")
            return

        issue = issues[0]
        key = issue['key']
        print(f"Inspecting Issue: {key}")
        print(json.dumps(issue['fields']['issuetype'], indent=2))
        print(json.dumps(issue['fields']['status'], indent=2))
        
        # 2. Check Transitions for this issue
        print(f"\nFetching Transitions for {key}...")
        trans_url = f"{JIRA_HOST}/rest/api/2/issue/{key}/transitions"
        t_resp = requests.get(trans_url, headers=get_jira_headers(), auth=get_jira_auth())
        
        if t_resp.status_code == 200:
            data = t_resp.json()
            print("Available Transitions:")
            for t in data.get('transitions', []):
                print(f"- ID: {t['id']}, Name: {t['name']}")
        else:
             print(f"Error fetching transitions: {t_resp.status_code}")

    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    inspect_issue()
