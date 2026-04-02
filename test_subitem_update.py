import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

MONDAY_TOKEN = os.getenv("MONDAY_API_TOKEN")
MONDAY_SUBITEM_BOARD_ID = "18393136039"

def get_monday_headers():
    return {
        "Authorization": MONDAY_TOKEN,
        "API-Version": "2023-10",
        "Content-Type": "application/json"
    }

def update_monday_subitem_status(item_id, status_index):
    url = "https://api.monday.com/v2"
    
    col_vals = json.dumps({
        "status": {"index": int(status_index)}
    }).replace('"', '\\"')
    
    query = f'''
    mutation {{
        change_multiple_column_values (item_id: {item_id}, board_id: {MONDAY_SUBITEM_BOARD_ID}, column_values: "{col_vals}") {{
            id
            column_values {{
                id
                text
            }}
        }}
    }}
    '''
    try:
        resp = requests.post(url, json={"query": query}, headers=get_monday_headers())
        print(json.dumps(resp.json(), indent=2))
    except Exception as e:
        print(f"Error: {e}")

# Test updating subitem 10848416812 to "Working on it" (Index 0)
print("Updating subitem 10848416812 to Status Index 0 (Working on it)...")
update_monday_subitem_status(10848416812, 0)
