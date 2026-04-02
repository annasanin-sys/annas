import os
import json
import requests
from dotenv import load_dotenv
import datetime

load_dotenv()

JIRA_HOST = os.getenv("JIRA_HOST").rstrip('/')
JIRA_EMAIL = os.getenv("JIRA_USER_EMAIL")
JIRA_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_PROJECT = os.getenv("JIRA_PROJECT_KEY")

MONDAY_TOKEN = os.getenv("MONDAY_API_TOKEN")
MONDAY_BOARD_ID = os.getenv("MONDAY_BOARD_ID")

SYNC_DB_FILE = "sync_db.json"

def get_jira_auth():
    return (JIRA_EMAIL, JIRA_TOKEN)

def get_jira_headers():
    return {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

def load_db():
    if os.path.exists(SYNC_DB_FILE):
        with open(SYNC_DB_FILE, 'r') as f:
            return json.load(f)
    return {"jira_to_monday": {}, "monday_to_jira": {}}

def fetch_recent_subtasks():
    # Fetch ANY issue to check connectivity and issue types
    jql = f"project = {JIRA_PROJECT}"
    url = f"{JIRA_HOST}/rest/api/3/search/jql"
    
    print(f"Fetching ANY issues using JQL: {jql}")
    
    payload = {
        "jql": jql,
        "fields": ["summary", "status", "issuetype", "parent"],
        "maxResults": 10
    }
    
    try:
        resp = requests.post(url, json=payload, headers=get_jira_headers(), auth=get_jira_auth())
        resp.raise_for_status()
        return resp.json().get("issues", [])
    except Exception as e:
        print(f"[ERROR] Fetching Jira issues: {e}")
        return []

def check_sync_status():
    db = load_db()
    subtasks = fetch_recent_subtasks()
    
    print(f"Found {len(subtasks)} recent subtasks.")
    
    for sub in subtasks:
        key = sub['key']
        summary = sub['fields']['summary']
        issue_type = sub['fields'].get('issuetype', {}).get('name')
        is_subtask = sub['fields'].get('issuetype', {}).get('subtask')
        
        print(f"\nEvaluating Issue: {key} - {summary}")
        print(f"  Type: {issue_type} (Subtask Flag: {is_subtask})")
        
        if not is_subtask:
            continue

        parent = sub['fields'].get('parent', {})
        parent_key = parent.get('key')
        
        print(f"\nEvaluating Subtask: {key} - {summary}")
        print(f"  Parent: {parent_key}")
        
        # Check DB Mapping
        mapped_id = db['jira_to_monday'].get(key)
        print(f"  Mapped in DB? {'YES -> ' + str(mapped_id) if mapped_id else 'NO'}")
        
        # Check Parent Mapping
        mapped_parent_id = db['jira_to_monday'].get(parent_key)
        print(f"  Parent Mapped in DB? {'YES -> ' + str(mapped_parent_id) if mapped_parent_id else 'NO'}")
        
        if not mapped_parent_id:
            print("  [FAIL] Parent not mapped. Subtask cannot sync.")
            continue
            
        # If mapped, check if exists on Monday
        if mapped_id:
            # Check ID
            pass
            
if __name__ == "__main__":
    check_sync_status()
