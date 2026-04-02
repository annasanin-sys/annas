
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

JIRA_PROJECT = os.getenv("JIRA_PROJECT_KEY")

def fetch_one_subtask():
    url = f"{JIRA_HOST}/rest/api/3/search/jql"
    # Filter by Project to ensure we see them
    jql = f"project = {JIRA_PROJECT} AND issuetype in (Sub-task, Subtask) ORDER BY created DESC"
    payload = {
        "jql": jql,
        "maxResults": 1,
        "fields": ["summary", "status", "issuetype"]
    }
    resp = requests.post(url, json=payload, headers=get_jira_headers(), auth=get_jira_auth())
    resp.raise_for_status()
    issues = resp.json().get("issues", [])
    if issues:
        return issues[0]
    return None

def fetch_monday_item(item_id):
    url = "https://api.monday.com/v2"
    query = f'''
    query {{
        items (ids: [{item_id}]) {{
            id
            name
            column_values {{
                id
                text
                ... on StatusValue {{
                    index
                    label
                }}
            }}
        }}
    }}
    '''
    resp = requests.post(url, json={"query": query}, headers=get_monday_headers())
    return resp.json().get("data", {}).get("items", [])

def update_monday_item(item_id, status_index):
    url = "https://api.monday.com/v2"
    
    col_vals = json.dumps({
        "status": {"index": int(status_index)}
    }).replace('"', '\\"')
    
    query = f'''
    mutation {{
        change_multiple_column_values (item_id: {item_id}, board_id: {MONDAY_SUBITEM_BOARD_ID}, column_values: "{col_vals}") {{
            id
        }}
    }}
    '''
    print(f"Sending Mutation: {query}")
    resp = requests.post(url, json={"query": query}, headers=get_monday_headers())
    print("Response:", resp.json())
    return resp.json()

def main():
    pass
    # 1. Get Jira Subtask
    sub = fetch_one_subtask()
    if not sub:
        print("No subtasks found in Jira.")
        return
    
    key = sub['key']
    jira_status = sub['fields']['status']['name']
    print(f"Found Jira Subtask: {key} | Status: {jira_status}")
    
    # 2. Check DB
    try:
        with open("sync_db.json", "r") as f:
            db = json.load(f)
    except:
        print("No DB found.")
        return

    m_id = db['jira_to_monday'].get(key)
    if not m_id:
        print(f"Subtask {key} not synced to Monday (not in DB).")
        return
    
    print(f"Mapped to Monday ID: {m_id}")
    
    # 3. Fetch Monday Item
    items = fetch_monday_item(m_id)
    if not items:
        print("Item not found on Monday.")
        return
    
    m_item = items[0]
    print(f"Monday Item Name: {m_item['name']}")
    curr_status = "N/A"
    curr_index = -1
    for col in m_item['column_values']:
        if col['id'] == 'status':
            curr_status = col['text']
            curr_index = col.get('index')
            print(f"Current Monday Status: {curr_status} (Index {curr_index})")
    
    # 4. Attempt Update
    # Toggle status: 1 (Done) <-> 0 (Working on it)
    new_index = 0 if curr_index != 0 else 1
    print(f"Attempting to update to Index {new_index}...")
    
    update_monday_item(m_id, new_index)
    
    # 5. Verify
    items_after = fetch_monday_item(m_id)
    for col in items_after[0]['column_values']:
        if col['id'] == 'status':
            print(f"Post-Update Monday Status: {col['text']} (Index {col.get('index')})")

if __name__ == "__main__":
    main()
