import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

JIRA_HOST = os.getenv("JIRA_HOST").rstrip('/')
JIRA_EMAIL = os.getenv("JIRA_USER_EMAIL")
JIRA_TOKEN = os.getenv("JIRA_API_TOKEN")
MONDAY_TOKEN = os.getenv("MONDAY_API_TOKEN")
MONDAY_SUBITEM_BOARD_ID = "18393136039"
SYNC_DB_FILE = "sync_db.json"

def get_jira_auth(): return (JIRA_EMAIL, JIRA_TOKEN)
def get_jira_headers(): return {"Accept": "application/json", "Content-Type": "application/json"}
def get_monday_headers(): return {"Authorization": MONDAY_TOKEN, "API-Version": "2023-10", "Content-Type": "application/json"}

def load_db():
    if os.path.exists(SYNC_DB_FILE):
        with open(SYNC_DB_FILE, 'r') as f: return json.load(f)
    return {"jira_to_monday": {}, "monday_to_jira": {}}

def save_db(db):
    with open(SYNC_DB_FILE, 'w') as f: json.dump(db, f, indent=4)

def fetch_issue(key):
    url = f"{JIRA_HOST}/rest/api/3/issue/{key}"
    resp = requests.get(url, headers=get_jira_headers(), auth=get_jira_auth())
    return resp.json()

def create_monday_subitem(parent_id, title, status_index):
    url = "https://api.monday.com/v2"
    col_vals = json.dumps({"status": {"index": int(status_index)}}).replace('"', '\\"')
    query = f'''
    mutation {{
        create_subitem (parent_item_id: {parent_id}, item_name: "{title}", column_values: "{col_vals}") {{
            id
        }}
    }}
    '''
    resp = requests.post(url, json={"query": query}, headers=get_monday_headers())
    print(f"Create response: {resp.text}")
    return resp.json().get("data", {}).get("create_subitem", {})

def force_sync():
    key = "AC-3880"
    print(f"Force syncing {key}...")
    
    issue = fetch_issue(key)
    summary = issue['fields']['summary']
    status = issue['fields']['status']['name']
    parent_key = issue['fields']['parent']['key']
    
    print(f"  Summary: {summary}")
    print(f"  Status: {status}")
    print(f"  Parent: {parent_key}")
    
    db = load_db()
    
    if parent_key not in db['jira_to_monday']:
        print("[ERROR] Parent not in DB! Cannot sync.")
        return

    monday_parent_id = db['jira_to_monday'][parent_key]
    print(f"  Monday Parent ID: {monday_parent_id}")
    
    # Status Map
    monday_status_idx = "5" # To Do
    if status == "In Progress": monday_status_idx = "0"
    if status == "Done": monday_status_idx = "1"
    
    title = f"[{key}] {summary}"
    
    sub = create_monday_subitem(monday_parent_id, title, monday_status_idx)
    if sub:
        m_id = sub['id']
        print(f"  Created Monday Subitem: {m_id}")
        db['jira_to_monday'][key] = m_id
        db['monday_to_jira'][m_id] = key
        save_db(db)
        print("  DB Updated.")

if __name__ == "__main__":
    force_sync()
