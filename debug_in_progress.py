import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

JIRA_HOST = os.getenv("JIRA_HOST").rstrip('/')
JIRA_EMAIL = os.getenv("JIRA_USER_EMAIL")
JIRA_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_PROJECT = os.getenv("JIRA_PROJECT_KEY")
MONDAY_TOKEN = os.getenv("MONDAY_API_TOKEN")
MONDAY_BOARD_ID = os.getenv("MONDAY_BOARD_ID")

def get_jira_auth():
    return (JIRA_EMAIL, JIRA_TOKEN)

def get_jira_headers():
    return {"Accept": "application/json", "Content-Type": "application/json"}

def get_monday_headers():
    return {"Authorization": MONDAY_TOKEN, "API-Version": "2023-10", "Content-Type": "application/json"}

def fetch_in_progress_jira():
    jql = f"project = {JIRA_PROJECT} AND status = 'In Progress'"
    url = f"{JIRA_HOST}/rest/api/3/search/jql"
    payload = {
        "jql": jql,
        "fields": ["summary", "status", "issuetype", "parent"],
        "maxResults": 50
    }
    try:
        resp = requests.post(url, json=payload, headers=get_jira_headers(), auth=get_jira_auth())
        resp.raise_for_status()
        return resp.json().get("issues", [])
    except Exception as e:
        print(f"Jira Error: {e}")
        return []

def fetch_monday_items_map_paginated():
    url = "https://api.monday.com/v2"
    item_map = {} # name -> {id, status_idx, status_label}
    cursor = None
    
    print("Fetching Monday items (Paginated)...")
    while True:
        if cursor:
             query = f'query {{ boards (ids: {MONDAY_BOARD_ID}) {{ items_page (cursor: "{cursor}", limit: 100) {{ cursor items {{ id name column_values {{ id text ... on StatusValue {{ index label }} }} }} }} }} }}'
        else:
             query = f'query {{ boards (ids: {MONDAY_BOARD_ID}) {{ items_page (limit: 100) {{ cursor items {{ id name column_values {{ id text ... on StatusValue {{ index label }} }} }} }} }} }}'
        
        try:
            resp = requests.post(url, json={"query": query}, headers=get_monday_headers())
            data = resp.json()
            board = data.get('data', {}).get('boards', [{}])[0]
            items = board.get('items_page', {}).get('items', [])
            cursor = board.get('items_page', {}).get('cursor')
            
            for i in items:
                status_val = next((c for c in i['column_values'] if c['id'] == 'status'), {})
                item_map[i['name']] = {
                    "id": i['id'],
                    "status_idx": status_val.get('index'),
                    "status_label": status_val.get('label')
                }
            
            print(f"  Batch: {len(items)}. Map size: {len(item_map)}")
            if not cursor: break
        except Exception as e:
            print(f"Monday Error: {e}")
            break
            
    return item_map

print("--- Debugging In Progress Tasks ---")
jira_issues = fetch_in_progress_jira()
print(f"Found {len(jira_issues)} 'In Progress' issues in Jira (Limited to 50)")

monday_map = fetch_monday_items_map_paginated()

print("\n--- Comparing ---")
for issue in jira_issues:
    key = issue['key']
    summary = issue['fields']['summary']
    is_subtask = issue['fields']['issuetype']['subtask']
    
    # Expected Monday Name
    if is_subtask:
        # Check logic from sync_script: 
        # Naming logic: if startswith [KEY], use it, else add it.
        # But wait, subtasks in Monday might be just the summary if they are subitems?
        # In sync_script: 
        # monday_title = f"[{key}] {summary}"
        # But for subitems, does it check the name on the Main board or Subitem board?
        # The map I fetched is MAIN BOARD. Subitems are on a separate board (or `subitems` field).
        
        # This debug script only fetches MAIN BOARD items. 
        # If the user is talking about subtasks "In Progress", they might be on the subitem board.
        pass
    
    # Ideally should match: "[KEY] Summary"
    target_name = f"[{key}] {summary}"
    
    if target_name in monday_map:
        m_item = monday_map[target_name]
        print(f"[MATCH] {key} found. Monday Status: {m_item['status_label']} (Idx: {m_item['status_idx']})")
    else:
        # Try finding by key
        found = False
        for m_name, m_data in monday_map.items():
            if m_name.startswith(f"[{key}]"):
                print(f"[MATCH-ish] {key} found as '{m_name}'. Monday Status: {m_data['status_label']}")
                found = True
                break
        if not found:
            if is_subtask:
                 print(f"[MISSING] {key} (Subtask) not found on Main Board (Expected if it's a subitem).")
            else:
                 print(f"[MISSING] {key} (Parent) not found on Monday!")
