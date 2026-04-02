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

def inspect_monday_subitems(parent_item_id):
    print(f"--- Inspecting Monday Subitems for Parent {parent_item_id} ---")
    url = "https://api.monday.com/v2"
    
    # query to get subitems
    query = f'''
    query {{
        items (ids: [{parent_item_id}]) {{
            id
            name
            subitems {{
                id
                name
                column_values {{
                    id
                    text
                }}
            }}
        }}
    }}
    '''
    
    try:
        resp = requests.post(url, json={"query": query}, headers=get_monday_headers())
        if resp.status_code != 200:
            print(f"Error: {resp.status_code} - {resp.text}")
            return

        data = resp.json()
        items = data.get('data', {}).get('items', [])
        if not items:
            print("Parent item not found in Monday.")
            return

        parent = items[0]
        print(f"Parent Name: {parent['name']}")
        subitems = parent.get('subitems', [])
        print(f"Subitems Count: {len(subitems)}")
        
        for sub in subitems:
            print(f"  - [{sub['id']}] {sub['name']}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    # We will pass the ID found from grep here
    # Placeholder, will be replaced by user or subsequent call
    pass
