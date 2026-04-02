import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

JIRA_HOST = os.getenv("JIRA_HOST").rstrip('/')
JIRA_EMAIL = os.getenv("JIRA_USER_EMAIL")
JIRA_TOKEN = os.getenv("JIRA_API_TOKEN")
MONDAY_TOKEN = os.getenv("MONDAY_API_TOKEN")
JIRA_KEY = "AC-4003"
EXPECTED_PARENT_ID = 11167888169 # ID for AC-3993 from diagnosis

def get_jira_auth():
    return (JIRA_EMAIL, JIRA_TOKEN)

def get_jira_headers():
    return {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

def get_monday_headers():
    return {
        "Authorization": MONDAY_TOKEN,
        "API-Version": "2023-10",
        "Content-Type": "application/json"
    }

def extract_text_from_adf(adf_body):
    if not adf_body: return ""
    try:
        if isinstance(adf_body, str): return adf_body 
        if 'content' not in adf_body: return ""
        text_lines = []
        for node in adf_body['content']:
            text_lines.append(extract_node_text(node))
        return "\\n".join(filter(None, text_lines))
    except:
        return ""

def extract_node_text(node):
    text = ""
    if 'text' in node: text += node['text']
    if 'content' in node:
        for child in node['content']:
            text += extract_node_text(child)
    return text

def fetch_jira_checklist_content(issue_key):
    url = f"{JIRA_HOST}/rest/api/3/issue/{issue_key}/properties/checklist"
    try:
        resp = requests.get(url, headers=get_jira_headers(), auth=get_jira_auth())
        if resp.status_code == 200:
            data = resp.json()
            return data.get('value', {}).get('items', "")
        return None
    except Exception as e:
        print(f"[ERROR] Fetching checklist for {issue_key}: {e}")
        return None

def create_monday_update(item_id, text_body):
    url = "https://api.monday.com/v2"
    query = f'''
    mutation {{
        create_update (item_id: {item_id}, body: "{text_body}") {{
            id
        }}
    }}
    '''
    try:
        resp = requests.post(url, json={"query": query}, headers=get_monday_headers())
        print(f"Update Response: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"Update Exception: {e}")


def create_monday_subitem(parent_id, title, status_label_index="5"): 
    # Defaulting to 5 (To Do) as per user observation
    url = "https://api.monday.com/v2"
    
    col_vals = json.dumps({
        "status": {"index": int(status_label_index)}
    }).replace('"', '\\"')

    query = f'''
    mutation {{
        create_subitem (parent_item_id: {parent_id}, item_name: "{title}", column_values: "{col_vals}") {{
            id
        }}
    }}
    '''
    try:
        resp = requests.post(url, json={"query": query}, headers=get_monday_headers())
        resp.raise_for_status()
        data = resp.json()
        print(f"Create Response: {data}")
        return data.get("data", {}).get("create_subitem", {})
    except Exception as e:
        print(f"[ERROR] Creating Monday subitem: {e}")
        return None

def force_sync():
    print(f"--- Force Syncing {JIRA_KEY} ---")
    
    # 1. Fetch Jira to get details
    url = f"{JIRA_HOST}/rest/api/3/issue/{JIRA_KEY}"
    resp = requests.get(url, headers=get_jira_headers(), auth=get_jira_auth())
    if resp.status_code != 200:
        print(f"[ERROR] Could not fetch Jira issue: {resp.text}")
        return

    data = resp.json()
    summary = data['fields']['summary']
    status = data['fields']['status']['name']
    
    print(f"Jira Data: {summary} ({status})")
    
    # Map Status (Quick Map based on sync_script.py)
    # "To Do": "5", "In Progress": "0", "Done": "1"
    status_map = {
        "To Do": "5",
        "In Progress": "0",
        "Done": "1"
    }
    monday_status_idx = status_map.get(status, "5")
    
    # Create Title
    title = f"[{JIRA_KEY}] {summary}"
    
    
    # 2. PROCEED TO CREATE (or Update if exists)
    print(f"Creating/Updating item on Monday under parent {EXPECTED_PARENT_ID}...")
    
    # Check if already created (from previous run)
    existing_id = None
    if os.path.exists("sync_db.json"):
        with open("sync_db.json", 'r') as f:
            db = json.load(f)
            existing_id = db['jira_to_monday'].get(JIRA_KEY)

    new_id = existing_id
    if not existing_id:
        new_item = create_monday_subitem(EXPECTED_PARENT_ID, title, monday_status_idx)
        if new_item:
            new_id = new_item['id']
            print(f"SUCCESS: Created Subitem {new_id}")
    else:
        print(f"Subitem already exists: {existing_id}. Proceeding to sync details.")
    
    if new_id:
        # 3. Sync Description
        desc_adf = data['fields'].get('description')
        desc_text = extract_text_from_adf(desc_adf)
        if desc_text and desc_text.strip():
             print(f"  -> Posting Description Update...")
             create_monday_update(new_id, f"**Synced Description:**\\n{desc_text}")
        
        # 4. Sync Checklist
        checklist_content = fetch_jira_checklist_content(JIRA_KEY)
        if checklist_content:
            print(f"  -> Syncing Checklist to Column...")
            MONDAY_CHECKLIST_COLUMN_ID = "long_text_mkyyh8gb" # Hardcoded from main script
            MONDAY_SUBITEM_BOARD_ID = "18393136039"
            col_vals = json.dumps({MONDAY_CHECKLIST_COLUMN_ID: checklist_content}).replace('"', '\\"')
            
            query_checklist = f'''
            mutation {{
                change_multiple_column_values (item_id: {new_id}, board_id: {MONDAY_SUBITEM_BOARD_ID}, column_values: "{col_vals}") {{
                    id
                }}
            }}
            '''
            try:
                requests.post("https://api.monday.com/v2", json={"query": query_checklist}, headers=get_monday_headers())
            except Exception as e:
                print(f"Failed to sync checklist: {e}")

        # 5. Update DB
        db_file = "sync_db.json"
        if not existing_id and os.path.exists(db_file):
            try:
                with open(db_file, 'r') as f:
                    db = json.load(f)
                
                db['jira_to_monday'][JIRA_KEY] = new_id
                db['monday_to_jira'][new_id] = JIRA_KEY
                
                with open(db_file, 'w') as f:
                    json.dump(db, f, indent=4)
                print("Updated sync_db.json")
            except Exception as e:
                print(f"Failed to update DB: {e}")
    else:
        print("Failed to create item.")

if __name__ == "__main__":
    force_sync()
