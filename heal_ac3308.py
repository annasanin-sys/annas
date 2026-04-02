import os
import requests
import json
import re
from dotenv import load_dotenv

load_dotenv()

MONDAY_TOKEN = os.getenv("MONDAY_API_TOKEN")
SYNC_DB_FILE = "sync_db.json"

def load_db():
    if os.path.exists(SYNC_DB_FILE):
        with open(SYNC_DB_FILE, 'r') as f:
            return json.load(f)
    return {"jira_to_monday": {}, "monday_to_jira": {}, "last_sync": None}

def save_db(db):
    with open(SYNC_DB_FILE, 'w') as f:
        json.dump(db, f, indent=4)

def get_monday_headers():
    return {"Authorization": MONDAY_TOKEN, "API-Version": "2023-10", "Content-Type": "application/json"}

def heal_ac3308():
    parent_jira = "AC-3308"
    parent_monday = "10847888161"
    
    print(f"--- Healing DB for {parent_jira} <-> {parent_monday} ---")
    
    db = load_db()
    
    # 1. Link Parent
    print(f"Linking Parent: {parent_jira} -> {parent_monday}")
    db['jira_to_monday'][parent_jira] = parent_monday
    db['monday_to_jira'][parent_monday] = parent_jira
    
    # 2. Fetch Subitems to Link Children
    url = "https://api.monday.com/v2"
    query = f'''
    query {{
        items (ids: [{parent_monday}]) {{
            subitems {{
                id
                name
            }}
        }}
    }}
    '''
    
    resp = requests.post(url, json={"query": query}, headers=get_monday_headers())
    data = resp.json()
    subitems = data.get('data', {}).get('items', [{}])[0].get('subitems', [])
    
    print(f"Found {len(subitems)} subitems on Monday. Scanning for keys...")
    
    linked_count = 0
    for sub in subitems:
        # Regex to find [AC-XXXX]
        match = re.search(r"\[(AC-\d+)\]", sub['name'])
        if match:
            jira_key = match.group(1)
            monday_id = sub['id']
            
            # Link
            db['jira_to_monday'][jira_key] = monday_id
            db['monday_to_jira'][monday_id] = jira_key
            print(f"  Mapped {jira_key} -> {monday_id}")
            linked_count += 1
        else:
            print(f"  [WARN] No Key found in name: '{sub['name']}' (ID: {sub['id']})")
            
    print(f"Total linked subitems: {linked_count}")
    
    # 3. Save
    save_db(db)
    print("Database patched.")

if __name__ == "__main__":
    heal_ac3308()
