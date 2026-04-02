import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

MONDAY_TOKEN = os.getenv("MONDAY_API_TOKEN")
MONDAY_SUBITEM_BOARD_ID = "18393136039" 
# Need a valid subitem ID. 
# I will fetch one first.

def get_monday_headers():
    return {
        "Authorization": MONDAY_TOKEN,
        "API-Version": "2023-10",
        "Content-Type": "application/json"
    }

def test_monday_checklist_column():
    # 1. Fetch one subitem
    url = "https://api.monday.com/v2"
    query_fetch = f'''
    query {{
        boards (ids: {MONDAY_SUBITEM_BOARD_ID}) {{
            items_page (limit: 1) {{
                items {{
                    id
                    name
                    column_values {{
                        id
                        text
                    }}
                }}
            }}
        }}
    }}
    '''
    try:
        resp = requests.post(url, json={"query": query_fetch}, headers=get_monday_headers())
        data = resp.json()
        items = data.get('data', {}).get('boards', [])[0].get('items_page', {}).get('items', [])
        if not items:
            print("No subitems found to test.")
            return

        item = items[0]
        item_id = item['id']
        print(f"Testing on Subitem: {item['name']} ({item_id})")
        
        # 2. Update 'text_mkyyw0bk' (Checklist Progress?) 
        # Wait, usually the CONTENT is in a different column?
        # If 'Checklist Progress' is the ONLY checklist-related column, 
        # maybe the content is lost?
        # Or maybe 'text_mkyyw0bk' IS the content column but named weirdly?
        # Let's try writing a checklist string to it.
        
        checklist_markdown = "- [ ] Item 1\\n- [x] Item 2"
        col_vals = json.dumps({
            "text_mkyyw0bk": checklist_markdown
        }).replace('"', '\\"')
        
        query_update = f'''
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
        
        print("Sending Update...")
        resp = requests.post(url, json={"query": query_update}, headers=get_monday_headers())
        print(json.dumps(resp.json(), indent=2))
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_monday_checklist_column()
