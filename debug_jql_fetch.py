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

def test_fetch():
    print(f"Testing Bulk Fetch for project {JIRA_PROJECT}...")
    jql = f"project = {JIRA_PROJECT}"
    
    next_token = None
    has_more = True
    max_results = 100 
    
    url = f"{JIRA_HOST}/rest/api/3/search/jql"
    
    found = False
    total_fetched = 0
    
    while has_more:
        payload = {
            "jql": jql,
            "fields": ["summary", "issuetype"],
            "maxResults": max_results
        }
        if next_token:
            payload["nextPageToken"] = next_token
        
        try:
            resp = requests.post(url, json=payload, headers=get_jira_headers(), auth=get_jira_auth())
            resp.raise_for_status()
            data = resp.json()
            
            issues_batch = data.get("issues", [])
            total_fetched += len(issues_batch)
            print(f"  Batch received: {len(issues_batch)} items.")
            
            for i in issues_batch:
                if i['key'] == 'AC-4003':
                    print(f"  [SUCCESS] Found AC-4003 in batch! IssueType: {i['fields']['issuetype']['name']}")
                    found = True
            
            next_token = data.get("nextPageToken")
            if not next_token or (data.get("isLast") is True):
                has_more = False
                
        except Exception as e:
            print(f"[ERROR] Fetch failed: {e}")
            break
            
    print(f"Total Fetched: {total_fetched}")
    if not found:
        print("[FAILURE] AC-4003 was NOT found in the bulk fetch results.")

if __name__ == "__main__":
    test_fetch()
