
import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

MONDAY_TOKEN = os.getenv("MONDAY_API_TOKEN")
MONDAY_BOARD_ID = os.getenv("MONDAY_BOARD_ID")
MONDAY_SUBITEM_BOARD_ID = "18393136039"

print(f"Main Board: {MONDAY_BOARD_ID}")
print(f"Subitem Board: {MONDAY_SUBITEM_BOARD_ID}")

def get_headers():
    return {
        "Authorization": MONDAY_TOKEN,
        "API-Version": "2023-10",
        "Content-Type": "application/json"
    }

def fetch_columns(board_id):
    query = f'''
    query {{
        boards (ids: {board_id}) {{
            columns {{
                id
                title
                type
                settings_str
            }}
        }}
    }}
    '''
    try:
        resp = requests.post("https://api.monday.com/v2", json={"query": query}, headers=get_headers())
        data = resp.json()
        return data.get('data', {}).get('boards', [{}])[0].get('columns', [])
    except Exception as e:
        print(f"Error fetching board {board_id}: {e}")
        return []

def print_status_columns(columns):
    for col in columns:
        if col['type'] == 'status': # status type
            print(f"  Column: {col['title']} (ID: {col['id']})")
            settings = json.loads(col['settings_str'])
            labels = settings.get('labels', {})
            # labels is usually map of index -> label
            # or sometimes key -> label
            print("    Labels:")
            for index, label in labels.items():
                print(f"      {index}: {label}")
            
            # customized label positions usually in 'labels_positions_v2' or similar
            # but mapping is ID based.
            
print("\n--- Main Board Columns ---")
main_cols = fetch_columns(MONDAY_BOARD_ID)
print_status_columns(main_cols)

print("\n--- Subitem Board Columns ---")
sub_cols = fetch_columns(MONDAY_SUBITEM_BOARD_ID)
print_status_columns(sub_cols)
