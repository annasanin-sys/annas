import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

JIRA_HOST = os.getenv("JIRA_HOST").rstrip('/')
JIRA_EMAIL = os.getenv("JIRA_USER_EMAIL")
JIRA_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_PROJECT = os.getenv("JIRA_PROJECT_KEY")

SYNC_DB_FILE = "sync_db.json"

def load_db():
    if os.path.exists(SYNC_DB_FILE):
        try:
            with open(SYNC_DB_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {"jira_to_monday": {}, "monday_to_jira": {}, "last_sync": None}

def get_jira_auth():
    return (JIRA_EMAIL, JIRA_TOKEN)

def get_jira_headers():
    return {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

def fetch_all_jira_subtasks():
    # Fetch ALL issues to match sync_script logic
    jql = f"project = {JIRA_PROJECT}"
    max_results = 100
    print(f"DEBUG: JQL = '{jql}'")
    
    subtasks = []
    
    url = f"{JIRA_HOST}/rest/api/3/search/jql"
    
    print("Fetching all Jira issues...")
    next_token = None
    has_more = True

    while has_more:
        payload = {
            "jql": jql,
            "fields": ["summary", "parent", "issuetype"],
            "maxResults": max_results
        }
        if next_token:
            payload["nextPageToken"] = next_token
        
        try:
            resp = requests.post(url, json=payload, headers=get_jira_headers(), auth=get_jira_auth())
            resp.raise_for_status()
            data = resp.json()
            
            issues = data.get("issues", [])
            for i in issues:
                if i['fields']['issuetype']['subtask']:
                    subtasks.append(i)
            print(f"  Fetched {len(issues)} (Found {len(subtasks)} subtasks so far)...")
            
            next_token = data.get("nextPageToken")
            if not next_token:
                has_more = False
            
        except Exception as e:
            print(f"[ERROR] {e}")
            break
            
    return subtasks

def diagnose_orphans():
    db = load_db()
    subtasks = fetch_all_jira_subtasks()
    
    orphans = [] # Subtasks whose parent is NOT in DB
    mapped_subtasks = 0
    
    print(f"\n--- Analysis of {len(subtasks)} Subtasks ---")
    
    for sub in subtasks:
        key = sub['key']
        parent = sub['fields'].get('parent')
        
        if not parent:
            print(f"  [WARN] Subtask {key} has no parent field!")
            continue
            
        parent_key = parent['key']
        
        # Check if parent is in DB
        if parent_key not in db['jira_to_monday']:
            orphans.append({
                "subtask": key,
                "parent": parent_key,
                "parent_summary": parent['fields']['summary']
            })
        else:
            mapped_subtasks += 1
            
    print(f"\nResults:")
    print(f"  Mapped Parents: {mapped_subtasks}")
    print(f"  ORPHANED (Parent missing from sync DB): {len(orphans)}")
    
    if orphans:
        print("\nTop 10 Orphaned Examples:")
        for o in orphans[:10]:
            print(f"  - Subtask {o['subtask']} (Parent {o['parent']}: {o['parent_summary']})")

if __name__ == "__main__":
    diagnose_orphans()
