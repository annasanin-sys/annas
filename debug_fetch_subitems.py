import requests
import os
from sync_script import get_monday_headers, MONDAY_SUBITEM_BOARD_ID

def fetch_subitems_test():
    url = "https://api.monday.com/v2"
    print(f"Fetching subitems from board {MONDAY_SUBITEM_BOARD_ID}...")
    
    query = f'''
    query {{
        boards (ids: {MONDAY_SUBITEM_BOARD_ID}) {{
            items_page (limit: 50) {{
                items {{
                    id
                    name
                    parent_item {{
                        id
                    }}
                }}
            }}
        }}
    }}
    '''
    
    try:
        resp = requests.post(url, json={"query": query}, headers=get_monday_headers())
        data = resp.json()
        print("Response:", data)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fetch_subitems_test()
