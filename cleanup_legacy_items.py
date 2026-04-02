import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

SYNC_DB_FILE = "sync_db.json"
JIRA_HOST = os.getenv("JIRA_HOST").rstrip('/')
JIRA_EMAIL = os.getenv("JIRA_USER_EMAIL")
JIRA_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_PROJECT = os.getenv("JIRA_PROJECT_KEY")
MONDAY_TOKEN = os.getenv("MONDAY_API_TOKEN")

def load_db():
    if os.path.exists(SYNC_DB_FILE):
        with open(SYNC_DB_FILE, 'r') as f:
            return json.load(f)
    return {"jira_to_monday": {}, "monday_to_jira": {}}

def save_db(db):
    with open(SYNC_DB_FILE, 'w') as f:
        json.dump(db, f, indent=4)

def get_jira_auth():
    return (JIRA_EMAIL, JIRA_TOKEN)

def get_jira_headers():
    return {"Accept": "application/json", "Content-Type": "application/json"}

def get_monday_headers():
    return {"Authorization": MONDAY_TOKEN, "API-Version": "2023-10", "Content-Type": "application/json"}

def fetch_all_jira_subtasks():
    # Fetch ONLY subtasks
    url = f"{JIRA_HOST}/rest/api/3/search/jql"
    payload = {
        "jql": f"project = {JIRA_PROJECT} AND issuetype = Sub-task",
        "fields": ["issuetype"],
        "maxResults": 200 # Should cover the ~91 mentioned
    }
    try:
        resp = requests.post(url, json=payload, headers=get_jira_headers(), auth=get_jira_auth())
        resp.raise_for_status()
        return resp.json().get("issues", [])
    except Exception as e:
        print(f"Error fetching Jira subtasks: {e}")
        return []

def archive_monday_item(item_id):
    url = "https://api.monday.com/v2"
    query = f'''
    mutation {{
        archive_item (item_id: {item_id}) {{
            id
        }}
    }}
    '''
    try:
        resp = requests.post(url, json={"query": query}, headers=get_monday_headers())
        if resp.status_code == 200:
            return True
        else:
            print(f"Failed to archive {item_id}: {resp.text}")
            return False
    except Exception as e:
        print(f"Exception archiving {item_id}: {e}")
        return False

def run_cleanup():
    db = load_db()
    subtasks = fetch_all_jira_subtasks()
    print(f"Found {len(subtasks)} subtasks in Jira.")
    
    count = 0
    for issue in subtasks:
        key = issue['key']
        # If this subtask is mapped in our DB, it means it's currently a Main Item on Monday (incorrect)
        if key in db['jira_to_monday']:
            m_id = db['jira_to_monday'][key]
            print(f"[{count+1}] Cleaning up {key} (Monday ID: {m_id})...")
            
            # 1. Archive on Monday
            if archive_monday_item(m_id):
                # 2. Remove from DB
                del db['jira_to_monday'][key]
                if m_id in db['monday_to_jira']:
                    del db['monday_to_jira'][m_id]
                count += 1
            else:
                print(f"Skipping DB removal for {key} due to API failure.")

    if count > 0:
        save_db(db)
        print(f"SUCCESS: cleaned up {count} legacy items.")
        print("Now run 'python sync_script.py' to re-sync them as Subitems.")
    else:
        print("No legacy items found to clean up.")

if __name__ == "__main__":
    run_cleanup()
