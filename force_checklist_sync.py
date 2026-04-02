import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

JIRA_HOST = os.getenv("JIRA_HOST").rstrip('/')
JIRA_EMAIL = os.getenv("JIRA_USER_EMAIL")
JIRA_TOKEN = os.getenv("JIRA_API_TOKEN")

MONDAY_TOKEN = os.getenv("MONDAY_API_TOKEN")
MONDAY_SUBITEM_BOARD_ID = "18393136039" 
MONDAY_CHECKLIST_COLUMN_ID = "long_text_mkyyh8gb"
TARGET_ISSUE_KEY = "AC-3309"
MONDAY_ITEM_ID = 10847888490 # Associated ID from previous output

def get_jira_headers():
    return {"Accept": "application/json", "Content-Type": "application/json"}

def get_jira_auth():
    return (JIRA_EMAIL, JIRA_TOKEN)

def get_monday_headers():
    return {"Authorization": MONDAY_TOKEN, "API-Version": "2023-10", "Content-Type": "application/json"}

def fetch_jira_checklist_content(issue_key):
    url = f"{JIRA_HOST}/rest/api/3/issue/{issue_key}/properties/checklist"
    print(f"Fetching from {url}...")
    try:
        resp = requests.get(url, headers=get_jira_headers(), auth=get_jira_auth())
        if resp.status_code == 200:
            data = resp.json()
            val = data.get('value', {}).get('items', "")
            print(f"Fetched Checklist Data: {val[:50]}...")
            return val
        print(f"Checklist not found: {resp.status_code}")
        return None
    except Exception as e:
        print(f"Error fetching checklist: {e}")
        return None

def force_sync():
    content = fetch_jira_checklist_content(TARGET_ISSUE_KEY)
    if not content:
        print("No content to sync.")
        return

    print("Pushing to Monday...")
    col_vals = json.dumps({MONDAY_CHECKLIST_COLUMN_ID: content}).replace('"', '\\"')
    query = f'''
    mutation {{
        change_multiple_column_values (item_id: {MONDAY_ITEM_ID}, board_id: {MONDAY_SUBITEM_BOARD_ID}, column_values: "{col_vals}") {{
            id
            column_values (ids: ["{MONDAY_CHECKLIST_COLUMN_ID}"]) {{
                text
            }}
        }}
    }}
    '''
    try:
        resp = requests.post("https://api.monday.com/v2", json={"query": query}, headers=get_monday_headers())
        print(json.dumps(resp.json(), indent=2))
    except Exception as e:
        print(f"Monday Error: {e}")

if __name__ == "__main__":
    force_sync()
