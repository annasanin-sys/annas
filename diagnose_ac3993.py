import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

JIRA_HOST = os.getenv("JIRA_HOST").rstrip('/')
JIRA_EMAIL = os.getenv("JIRA_USER_EMAIL")
JIRA_TOKEN = os.getenv("JIRA_API_TOKEN")
MONDAY_TOKEN = os.getenv("MONDAY_API_TOKEN")
SYNC_DB_FILE = "sync_db.json"

def get_monday_headers():
    return {
        "Authorization": MONDAY_TOKEN,
        "API-Version": "2023-10",
        "Content-Type": "application/json"
    }

def load_db():
    if os.path.exists(SYNC_DB_FILE):
        with open(SYNC_DB_FILE, 'r') as f:
            return json.load(f)
    return {}

def fetch_monday_item(item_id):
    url = "https://api.monday.com/v2"
    query = f'''
    query {{
        items (ids: [{item_id}]) {{
            id
            name
            state
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
    return resp.json().get('data', {}).get('items', [None])[0]

def diagnose():
    db = load_db()
    jira_key = "AC-3993"
    
    # 1. Check DB Map
    print(f"--- Diagnosing {jira_key} ---")
    monday_id = db.get('jira_to_monday', {}).get(jira_key)
    print(f"Mapped Monday ID: {monday_id}")
    
    # 2. Fetch Jira
    print(f"Fetching Jira {jira_key}...")
    jira_url = f"{JIRA_HOST}/rest/api/3/issue/{jira_key}"
    jira_resp = requests.get(jira_url, headers={"Content-Type": "application/json"}, auth=(JIRA_EMAIL, JIRA_TOKEN))
    
    if jira_resp.status_code == 200:
        j_data = jira_resp.json()
        j_summary = j_data['fields']['summary']
        j_status = j_data['fields']['status']['name']
        print(f"Jira Summary: {j_summary}")
        print(f"Jira Status: {j_status}")
    else:
        print(f"Failed to fetch Jira: {jira_resp.status_code}")

    # 3. Fetch Monday
    if monday_id:
        print(f"Fetching Monday Item {monday_id}...")
        try:
            m_item = fetch_monday_item(monday_id)
            if m_item:
                print(f"Monday Name: {m_item['name']}")
                print(f"Monday State: {m_item['state']}")
                for col in m_item['column_values']:
                    if col['id'] == 'status':
                        print(f"Monday Status: {col['text']} (Index: {col.get('index')})")
                
                # Fetch Subitems
                url = "https://api.monday.com/v2"
                query = f'''
                query {{
                    items (ids: [{monday_id}]) {{
                        subitems {{
                            id
                            name
                            updates {{
                                body
                                created_at
                            }}
                            column_values {{
                                id
                                ... on StatusValue {{
                                    index
                                    label
                                }}
                            }}
                        }}
                    }}
                }}
                '''
                resp = requests.post(url, json={"query": query}, headers=get_monday_headers())
                sub_data = resp.json().get('data', {}).get('items', [{}])[0].get('subitems', [])
                print(f"Monday Subitems ({len(sub_data)}):")
                for sub in sub_data:
                    status = "N/A"
                    for col in sub['column_values']:
                        if col['id'] == 'status':
                            status = col.get('label', 'N/A')
                    print(f"  - [{sub['id']}] {sub['name']} ({status})")
                    if sub.get('updates'):
                        print(f"    Updates: {len(sub['updates'])}")
                        for u in sub['updates']:
                             print(f"      - {u['body'][:50]}...")


            else:
                print("Monday Item not found (API returned empty/null).")
        except Exception as e:
            print(f"Error fetching Monday: {e}")
    else:
        print("No Monday ID mapped. Sync required.")

    # 4. Jira Subtasks
    if jira_resp.status_code == 200:
        subtasks = j_data['fields'].get('subtasks', [])
        print(f"Jira Subtasks ({len(subtasks)}):")
        for sub in subtasks:
             print(f"  - {sub['key']}: {sub['fields']['summary']} (Status: {sub['fields']['status']['name']})")


if __name__ == "__main__":
    diagnose()
