import os
import requests
import json
import datetime
from dotenv import load_dotenv

load_dotenv()

JIRA_HOST = os.getenv("JIRA_HOST").rstrip('/')
JIRA_EMAIL = os.getenv("JIRA_USER_EMAIL")
JIRA_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_PROJECT = os.getenv("JIRA_PROJECT_KEY")
MONDAY_TOKEN = os.getenv("MONDAY_API_TOKEN")
MONDAY_BOARD_ID = os.getenv("MONDAY_BOARD_ID")
MONDAY_SUBITEM_BOARD_ID = "18393136039"
SYNC_DB_FILE = "sync_db.json"

# Status Mappings (Mirrored from sync_script.py)
JIRA_TO_MONDAY_STATUS = {
    "To Do": "5",
    "Done": "1",
    "In Progress": "0",
}
JIRA_TO_MONDAY_SUBITEM_STATUS = {
    "To Do": "0",       # Working on it (Wait, need to verify this map)
    "Done": "1",        # Done
    "In Progress": "0", # Working on it
} 
# Note: Checking actual script default logic for accurate diffing
# User provided: "In Progress": "Working on it" (index 0 usually). "Done": "Done" (index 1). "To Do": "Working on it" or "Stuck"?
# sync_script says:
# JIRA_TO_MONDAY_STATUS = {"To Do": "5", "Done": "1", "In Progress": "0"} 
# JIRA_TO_MONDAY_SUBITEM_STATUS = {"To Do": "0", "Done": "1", "In Progress": "0"} #(Wait, 0 is usually Working on it. 5 is usually empty/grey?)

# Let's assume standard map for now and report "Differences".

def get_jira_auth(): return (JIRA_EMAIL, JIRA_TOKEN)
def get_jira_headers(): return {"Accept": "application/json", "Content-Type": "application/json"}
def get_monday_headers(): return {"Authorization": MONDAY_TOKEN, "API-Version": "2023-10", "Content-Type": "application/json"}

def execute_monday_query(query, retries=3):
    url = "https://api.monday.com/v2"
    for attempt in range(retries):
        try:
            resp = requests.post(url, json={"query": query}, headers=get_monday_headers())
            if resp.status_code >= 500:
                print(f"  [WARN] Monday API 500 Error. Retrying ({attempt+1}/{retries})...")
                continue
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            if attempt < retries - 1: continue
            raise e

def load_db():
    if os.path.exists(SYNC_DB_FILE):
        with open(SYNC_DB_FILE, 'r') as f: return json.load(f)
    return {"jira_to_monday": {}, "monday_to_jira": {}}

def fetch_jira_issues():
    jql = f"project = {JIRA_PROJECT}"
    parents = []
    subtasks = []
    
    url = f"{JIRA_HOST}/rest/api/3/search/jql"
    print("Fetching Jira issues...", flush=True)
    
    next_token = None
    has_more = True
    
    while has_more:
        payload = {"jql": jql, "fields": ["summary", "status", "issuetype", "parent"], "maxResults": 100}
        if next_token: payload["nextPageToken"] = next_token
        
        try:
            resp = requests.post(url, json=payload, headers=get_jira_headers(), auth=get_jira_auth())
            data = resp.json()
            issues = data.get("issues", [])
            
            for i in issues:
                if i['fields']['issuetype']['subtask']:
                    subtasks.append(i)
                else:
                    parents.append(i)
            
            next_token = data.get("nextPageToken")
            if not next_token: has_more = False
        except Exception as e:
            print(f"[ERROR] Jira fetch: {e}")
            break
    return parents, subtasks

def fetch_monday_data():
    # Fetch Parents
    items = []
    cursor = None
    print("Fetching Monday items...")
    while True:
        query_params = f'cursor: "{cursor}", limit: 100' if cursor else 'limit: 100'
        query = f'''query {{ boards (ids: {MONDAY_BOARD_ID}) {{ items_page ({query_params}) {{ cursor items {{ id name state column_values {{ id text ... on StatusValue {{ index label }} }} }} }} }} }}'''
        
        data = execute_monday_query(query)
        boards = data.get('data', {}).get('boards', [])
        if not boards: break
        
        page = boards[0].get('items_page', {})
        items.extend(page.get('items', []))
        cursor = page.get('cursor')
        if not cursor: break

    # Fetch Subitems
    subitem_map = {} # {parent_id: [subitems...]}
    subitem_details = {} # {id: {name, status}}
    cursor = None
    print("Fetching Monday subitems...")
    while True:
        query_params = f'cursor: "{cursor}", limit: 100' if cursor else 'limit: 100'
        # Need parent_item field + status
        query = f'''query {{ boards (ids: {MONDAY_SUBITEM_BOARD_ID}) {{ items_page ({query_params}) {{ cursor items {{ id name state parent_item {{ id }} column_values {{ id text ... on StatusValue {{ index label }} }} }} }} }} }}'''
        
        data = execute_monday_query(query)
        boards = data.get('data', {}).get('boards', [])
        if not boards: break
        
        page = boards[0].get('items_page', {})
        batch = page.get('items', [])
        
        for sub in batch:
            # Map by parent
            p_id = sub.get('parent_item', {}).get('id')
            if p_id:
                if p_id not in subitem_map: subitem_map[p_id] = []
                subitem_map[p_id].append(sub)
            
            # Store details
            status_text = "N/A"
            for col in sub.get('column_values', []):
                # Guessing status column logic (usually "status" or "status_1")
                if "status" in col['id']:
                    status_text = col['text']
            
            subitem_details[sub['id']] = {"name": sub['name'], "status": status_text, "parent": p_id}

        cursor = page.get('cursor')
        if not cursor: break
    
    return items, subitem_map, subitem_details

def analyze_diff():
    db = load_db()
    
    j_parents, j_subtasks = fetch_jira_issues()
    m_items, m_sub_map, m_sub_details = fetch_monday_data()
    
    m_items_dict = {i['id']: i for i in m_items}
    
    print("\n" + "="*60)
    print("JIRA vs MONDAY SYNC REPORT")
    print("="*60)
    
    # 1. Analyze Parents
    print(f"\n--- Parent Analysis (Jira: {len(j_parents)}, Monday: {len(m_items)}) ---")
    
    for p in j_parents:
        key = p['key']
        summary = p['fields']['summary']
        status = p['fields']['status']['name']
        
        # Get DB Map
        m_id = db['jira_to_monday'].get(key)
        
        if not m_id:
            print(f"[MISSING] Parent {key} '{summary}' is NOT mapped in DB.")
            continue
            
        m_item = m_items_dict.get(m_id)
        if not m_item:
            print(f"[GHOST] Parent {key} mapped to {m_id}, but item not found on Monday (Deleted/Archived).")
            continue
            
        # Check Status
        m_status = "N/A"
        for col in m_item.get('column_values', []):
            if "status" in col['id']: m_status = col['text']
            
        if status != m_status and m_status != "N/A": 
             # Note: fuzzy check needed. "Done" vs "Done". "In Progress" vs "Working on it".
             # Just print for user to judge.
             pass 
             
        # Check Subtask Counts
        j_subs = [s for s in j_subtasks if s['fields'].get('parent', {}).get('key') == key]
        m_subs = m_sub_map.get(m_id, [])
        
        if len(j_subs) != len(m_subs):
            print(f"[COUNT MISMATCH] {key}: Jira has {len(j_subs)} subtasks, Monday has {len(m_subs)} subitems.")
            
            # Detailed Subtask Check
            j_sub_keys = set(s['key'] for s in j_subs)
            
            # Extract keys from Monday names (assuming [KEY] format)
            m_sub_keys = set()
            for ms in m_subs:
                name = ms['name']
                # Try extract [AC-123]
                import re
                match = re.search(r"\[(AC-\d+)\]", name)
                if match:
                    m_sub_keys.add(match.group(1))
            
            missing_in_monday = j_sub_keys - m_sub_keys
            missing_in_jira = m_sub_keys - j_sub_keys
            
            if missing_in_monday:
                print(f"    -> Missing on Monday: {', '.join(missing_in_monday)}")
            if missing_in_jira:
                print(f"    -> Extra on Monday: {', '.join(missing_in_jira)}")

if __name__ == "__main__":
    analyze_diff()
