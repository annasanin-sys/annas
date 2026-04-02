import json
import os
from sync_script import fetch_jira_issues, load_db, get_monday_headers
import requests

def check_monday_item_exists(item_id):
    url = "https://api.monday.com/v2"
    query = f'''
    query {{
        items (ids: [{item_id}]) {{
            id
            name
        }}
    }}
    '''
    try:
        resp = requests.post(url, json={"query": query}, headers=get_monday_headers())
        data = resp.json()
        items = data.get('data', {}).get('items', [])
        return len(items) > 0
    except:
        return False

def main():
    print("Loading DB...")
    db = load_db()
    
    print("Fetching Jira issues...")
    parents, subtasks = fetch_jira_issues()
    
    target_parent = "AC-1816"
    print(f"Looking for {target_parent}...")
    
    # Check Parent in DB
    if target_parent in db['jira_to_monday']:
        mid = db['jira_to_monday'][target_parent]
        print(f"Parent {target_parent} is in DB -> Monday ID: {mid}")
        exists = check_monday_item_exists(mid)
        print(f"  -> Exists on Monday? {exists}")
    else:
        print(f"Parent {target_parent} is NOT in DB.")

    # Find Subtasks
    child_subtasks = [s for s in subtasks if s['fields'].get('parent', {}).get('key') == target_parent]
    print(f"Found {len(child_subtasks)} subtasks for {target_parent}:")
    
    for sub in child_subtasks:
        key = sub['key']
        summary = sub['fields']['summary']
        print(f"\nSubtask: {key} - {summary}")
        
        if key in db['jira_to_monday']:
            mid = db['jira_to_monday'][key]
            print(f"  -> In DB -> Monday ID: {mid}")
            exists = check_monday_item_exists(mid)
            print(f"  -> Exists on Monday? {exists}")
        else:
            print(f"  -> NOT in DB.")

if __name__ == "__main__":
    main()
