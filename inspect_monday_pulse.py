import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

MONDAY_TOKEN = os.getenv("MONDAY_API_TOKEN")

def inspect_monday_item(item_id):
    print(f"--- Inspecting Monday Item {item_id} ---")
    url = "https://api.monday.com/v2"
    query = f'''
    query {{
        items (ids: [{item_id}]) {{
            id
            name
            updates {{
                body
            }}
            subitems {{
                id
                name
            }}
        }}
    }}
    '''
    try:
        resp = requests.post(url, json={"query": query}, headers={"Authorization": MONDAY_TOKEN, "API-Version": "2023-10"})
        data = resp.json()
        items = data.get('data', {}).get('items', [])
        if not items:
            print("Item not found.")
            return

        item = items[0]
        print(f"Name: {item['name']}")
        print(f"Subitems Count: {len(item.get('subitems', []))}")
        for sub in item.get('subitems', []):
            print(f"  - {sub['name']} (ID: {sub['id']})")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    inspect_monday_item("10847888161")
