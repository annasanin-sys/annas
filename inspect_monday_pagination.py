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

def fetch_monday_items_simple():
    url = "https://api.monday.com/v2"
    all_items = []
    cursor = None
    while True:
        # If we have a cursor, use it. Otherwise start fresh.
        if cursor:
            query = f'''
            query {{
                boards (ids: {MONDAY_BOARD_ID}) {{
                    items_page (cursor: "{cursor}", limit: 50) {{
                        cursor
                        items {{
                            id
                        }}
                    }}
                }}
            }}
            '''
        else:
            query = f'''
            query {{
                boards (ids: {MONDAY_BOARD_ID}) {{
                    items_page (limit: 50) {{
                        cursor
                        items {{
                            id
                        }}
                    }}
                }}
            }}
            '''
        
        try:
            resp = requests.post(url, json={"query": query}, headers=get_monday_headers())
            data = resp.json()
            board_data = data.get('data', {}).get('boards', [{}])[0]
            items = board_data.get('items_page', {}).get('items', [])
            cursor = board_data.get('items_page', {}).get('cursor')
            
            all_items.extend(items)
            print(f"Fetched {len(items)} items. Total: {len(all_items)}")
            
            if not cursor:
                break
            if len(all_items) > 100: # Safety break for test
                print("Stopping test at > 100 items.")
                break
                
        except Exception as e:
            print(f"Error: {e}")
            break
            
    return len(all_items), cursor, all_items[:5]

count, cursor, sample = fetch_monday_items_simple()
print(f"Total Fetched: {count}")

