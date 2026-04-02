import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

MONDAY_TOKEN = os.getenv("MONDAY_API_TOKEN")
MONDAY_BOARD_ID = os.getenv("MONDAY_BOARD_ID")

def get_monday_headers():
    return {
        "Authorization": MONDAY_TOKEN,
        "API-Version": "2023-10",
        "Content-Type": "application/json"
    }

def debug_create():
    url = "https://api.monday.com/v2"
    
    # 1. Get a Parent
    print("Fetching a parent item...")
    q_parent = f'''query {{ boards(ids: {MONDAY_BOARD_ID}) {{ items_page(limit:1) {{ items {{ id name }} }} }} }}'''
    r = requests.post(url, json={"query": q_parent}, headers=get_monday_headers())
    data = r.json()
    items = data.get('data', {}).get('boards', [{}])[0].get('items_page', {}).get('items', [])
    
    if not items:
        print("No parent items found! Please ensure at least one Main Item exists.")
        return

    parent_id = items[0]['id']
    parent_name = items[0]['name']
    print(f"Using Parent: {parent_name} (ID: {parent_id})")
    
    # 2. Try Creating Subitem with Status '0' (Working on it)
    print("\nAttempt 1: Creating Subitem with Status Index '0' (Working on it)")
    col_vals = json.dumps({"status": {"index": 0}}).replace('"', '\\"')
    q_create = f'''
    mutation {{
        create_subitem (parent_item_id: {parent_id}, item_name: "Debug Subitem - Status 0", column_values: "{col_vals}") {{
            id
            column_values {{
                id
                text
                value
            }}
        }}
    }}
    '''
    r = requests.post(url, json={"query": q_create}, headers=get_monday_headers())
    print("Response:", json.dumps(r.json(), indent=2))
    
    # 3. Try Creating Subitem with Status Index 1 (Done)
    print("\nAttempt 2: Creating Subitem with Status Index '1' (Done)")
    col_vals = json.dumps({"status": {"index": 1}}).replace('"', '\\"')
    q_create = f'''
    mutation {{
        create_subitem (parent_item_id: {parent_id}, item_name: "Debug Subitem - Status 1", column_values: "{col_vals}") {{
            id
            column_values {{
                id
                text
                value
            }}
        }}
    }}
    '''
    r = requests.post(url, json={"query": q_create}, headers=get_monday_headers())
    print("Response:", json.dumps(r.json(), indent=2))

if __name__ == "__main__":
    debug_create()
