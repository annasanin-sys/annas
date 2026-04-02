import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

MONDAY_TOKEN = os.getenv("MONDAY_API_TOKEN")

def get_monday_headers():
    return {
        "Authorization": MONDAY_TOKEN,
        "API-Version": "2023-10",
        "Content-Type": "application/json"
    }

def test_create_subitem(parent_item_id, subitem_name):
    url = "https://api.monday.com/v2"
    query = f'''
    mutation {{
        create_subitem (parent_item_id: {parent_item_id}, item_name: "{subitem_name}") {{
            id
            name
            board {{
                id
            }}
        }}
    }}
    '''
    try:
        print(f"Creating subitem '{subitem_name}' under parent {parent_item_id}...")
        resp = requests.post(url, json={"query": query}, headers=get_monday_headers())
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # We need a valid parent item ID. 
    # I'll try to fetch one first or let the user provide one.
    # For now, I'll fetch the first item from the board to use as a test parent.
    
    MONDAY_BOARD_ID = os.getenv("MONDAY_BOARD_ID")
    url = "https://api.monday.com/v2"
    query = f'''
    query {{
        boards (ids: {MONDAY_BOARD_ID}) {{
            items_page (limit: 1) {{
                items {{
                    id
                    name
                }}
            }}
        }}
    }}
    '''
    resp = requests.post(url, json={"query": query}, headers=get_monday_headers())
    items = resp.json().get('data', {}).get('boards', [{}])[0].get('items_page', {}).get('items', [])
    
    if items:
        parent_id = items[0]['id']
        print(f"Found parent item: {parent_id} ({items[0]['name']})")
        test_create_subitem(parent_id, "Test Subitem from Script")
    else:
        print("No items found to test subitem creation.")
