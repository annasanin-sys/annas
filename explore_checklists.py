import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

# --- Jira ---
JIRA_HOST = os.getenv("JIRA_HOST").rstrip('/')
JIRA_EMAIL = os.getenv("JIRA_USER_EMAIL")
JIRA_TOKEN = os.getenv("JIRA_API_TOKEN")

def get_jira_headers():
    return {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

def get_jira_auth():
    return (JIRA_EMAIL, JIRA_TOKEN)

def find_jira_fields():
    url = f"{JIRA_HOST}/rest/api/3/field"
    print(f"Fetching Jira fields from {url}...")
    try:
        resp = requests.get(url, headers=get_jira_headers(), auth=get_jira_auth())
        resp.raise_for_status()
        fields = resp.json()
        print(f"Found {len(fields)} fields. Searching for 'checklist'...")
        found = []
        for f in fields:
            if "checklist" in f['name'].lower() or "check" in f['name'].lower():
                found.append(f)
        
        for f in found:
            print(f"  [Jira] Name: '{f['name']}', ID: '{f['id']}', Type: '{f.get('schema', {}).get('type')}'")
            
    except Exception as e:
        print(f"Error fetching Jira fields: {e}")

# --- Monday ---
MONDAY_TOKEN = os.getenv("MONDAY_API_TOKEN")
# Using Subitem Board ID from sync_script.py
MONDAY_SUBITEM_BOARD_ID = "18393136039" 

def get_monday_headers():
    return {
        "Authorization": MONDAY_TOKEN,
        "API-Version": "2023-10",
        "Content-Type": "application/json"
    }

def find_monday_columns():
    url = "https://api.monday.com/v2"
    query = f'''
    query {{
        boards (ids: {MONDAY_SUBITEM_BOARD_ID}) {{
            columns {{
                id
                title
                type
            }}
        }}
    }}
    '''
    print(f"Fetching Monday columns for board {MONDAY_SUBITEM_BOARD_ID}...")
    try:
        resp = requests.post(url, json={"query": query}, headers=get_monday_headers())
        data = resp.json()
        boards = data.get('data', {}).get('boards', [])
        if boards:
            cols = boards[0].get('columns', [])
            print(f"Found {len(cols)} columns. searching for checklist candidates...")
            for c in cols:
                print(f"  [Monday] Title: '{c['title']}', ID: '{c['id']}', Type: '{c['type']}'")
        else:
            print("No boards found or error in structure.")
            print(json.dumps(data, indent=2))
    except Exception as e:
        print(f"Error fetching Monday columns: {e}")

if __name__ == "__main__":
    find_jira_fields()
    print("-" * 20)
    find_monday_columns()
