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

def get_jira_auth():
    return (JIRA_EMAIL, JIRA_TOKEN)

def debug_fetch():
    print("--- Starting Debug Fetch ---")
    jql = f"project = {JIRA_PROJECT}"
    
    parents = []
    subtasks = []
    
    next_token = None
    has_more = True
    max_results = 100 
    
    url = f"{JIRA_HOST}/rest/api/3/search/jql"
    
    batch_count = 0
    
    while has_more:
        batch_count += 1
        print(f"Fetching Batch {batch_count}...")
        payload = {
            "jql": jql,
            "fields": ["summary", "status", "issuetype", "parent"],
            "maxResults": max_results
        }
        if next_token:
            payload["nextPageToken"] = next_token
        
        try:
            resp = requests.post(url, json=payload, headers=get_jira_headers(), auth=get_jira_auth())
            resp.raise_for_status()
            data = resp.json()
            
            issues_batch = data.get("issues", [])
            print(f"  Got {len(issues_batch)} issues.")
            
            for i in issues_batch:
                key = i['key']
                if key == "AC-3274":
                    print(f"  !!! FOUND AC-3274 !!! Type: {i['fields']['issuetype']['name']}")
                    if 'parent' in i['fields']:
                        print(f"  Parent: {i['fields']['parent']['key']}")
                    else:
                        print("  NO PARENT FIELD FOUND")

                if i['fields']['issuetype']['subtask']:
                    subtasks.append(i)
                else:
                    parents.append(i)
            
            next_token = data.get("nextPageToken")
            if not next_token or (data.get("isLast") is True):
                has_more = False
                
        except Exception as e:
            print(f"[ERROR] Fetching Jira issues: {e}")
            break
            
    print(f"Total Parents: {len(parents)}")
    print(f"Total Subtasks: {len(subtasks)}")

if __name__ == "__main__":
    debug_fetch()
