
import os
import json
import requests
import time
from dotenv import load_dotenv

load_dotenv()

MONDAY_TOKEN = os.getenv("MONDAY_API_TOKEN")
MONDAY_BOARD_ID = os.getenv("MONDAY_BOARD_ID")
# Using the subitem board ID from sync_script.py
MONDAY_SUBITEM_BOARD_ID = "18393136039" 

def get_headers():
    return {
        "Authorization": MONDAY_TOKEN,
        "API-Version": "2023-10",
        "Content-Type": "application/json"
    }

def create_item(board_id, name):
    query = f'''
    mutation {{
        create_item (board_id: {board_id}, item_name: "{name}") {{
            id,
            column_values {{
                id
                text
            }}
        }}
    }}
    '''
    resp = requests.post("https://api.monday.com/v2", json={"query": query}, headers=get_headers())
    return resp.json().get('data', {}).get('create_item')

def update_monday_item(item_id, status_label_index, board_id):
    col_vals = json.dumps({"status": {"index": int(status_label_index)}}).replace('"', '\\"')
    query = f'''
    mutation {{
        change_multiple_column_values (item_id: {item_id}, board_id: {board_id}, column_values: "{col_vals}") {{
            id
        }}
    }}
    '''
    print(f"Update Query: {query}")
    resp = requests.post("https://api.monday.com/v2", json={"query": query}, headers=get_headers())
    print(f"Update Resp: {resp.text}")
    return resp.json()

def get_item_status(item_id):
    query = f'''
    query {{
        items (ids: [{item_id}]) {{
            column_values(ids: ["status"]) {{
                ... on StatusValue {{
                    index
                    label
                }}
            }}
        }}
    }}
    '''
    resp = requests.post("https://api.monday.com/v2", json={"query": query}, headers=get_headers())
    data = resp.json()
    items = data.get('data', {}).get('items', [])
    if items:
        return items[0]['column_values'][0]
    return None

def delete_item(item_id):
    query = f'''
    mutation {{
        delete_item (item_id: {item_id}) {{
            id
        }}
    }}
    '''
    requests.post("https://api.monday.com/v2", json={"query": query}, headers=get_headers())

print("--- Starting Verify Status Update ---")
# 1. Create Test Item on Main Board
print("1. Creating Test Item...")
item = create_item(MONDAY_BOARD_ID, "Test Status Update")
if not item:
    print("Failed to create item.")
    exit()
    
item_id = item['id']
print(f"Item Created: {item_id}")

try:
    # 2. Check Initial Status (Should be default, likely 5/To Do or empty)
    print("2. Current Status:")
    print(get_item_status(item_id))
    
    # 3. Update to 'Done' (Index 1)
    print("3. Updating to 'Done' (Index 1)...")
    update_monday_item(item_id, 1, MONDAY_BOARD_ID)
    
    # 4. Verify
    print("4. verifying...")
    time.sleep(1) # Give it a moment?
    status = get_item_status(item_id)
    print(f"New Status: {status}")
    
    if status and status.get('index') == 1:
        print("SUCCESS: Status updated to Done.")
    else:
        print("FAILURE: Status did not update.")
        
finally:
    # 5. Cleanup
    print("5. Deleting Test Item...")
    delete_item(item_id)
