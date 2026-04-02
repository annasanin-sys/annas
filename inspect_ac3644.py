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

def inspect_ac3644():
    # 1. Fetch the parent issue directly
    issue_key = "AC-3644"
    print(f"--- Inspecting {issue_key} ---")
    url = f"{JIRA_HOST}/rest/api/3/issue/{issue_key}"
    
    try:
        resp = requests.get(url, headers=get_jira_headers(), auth=(JIRA_EMAIL, JIRA_TOKEN))
        if resp.status_code != 200:
            print(f"Error fetching parent: {resp.status_code} - {resp.text}")
            return
            
        data = resp.json()
        print(f"Summary: {data['fields']['summary']}")
        print(f"Status: {data['fields']['status']['name']}")
        subtasks = data['fields'].get('subtasks', [])
        print(f"Subtasks count in parent field: {len(subtasks)}")
        for sub in subtasks:
             print(f"  - {sub['key']}: {sub['fields']['summary']} (Status: {sub['fields']['status']['name']})")
             
        # 2. Search via JQL to see if they show up in search
        print("\n--- Searching via JQL ---")
        jql = f"parent = {issue_key}"
        search_url = f"{JIRA_HOST}/rest/api/3/search/jql"
        payload = {
            "jql": jql,
            "fields": ["summary", "status", "issuetype"],
            "maxResults": 100
        }
        resp_search = requests.post(search_url, json=payload, headers=get_jira_headers(), auth=(JIRA_EMAIL, JIRA_TOKEN))
        if resp_search.status_code == 200:
            search_data = resp_search.json()
            found_issues = search_data.get('issues', [])
            print(f"Subtasks found via JQL: {len(found_issues)}")
            for i in found_issues:
                print(f"  - {i['key']}: {i['fields']['summary']}")
        else:
             print(f"Error searching JQL: {resp_search.status_code} - {resp_search.text}")

    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    inspect_ac3644()
