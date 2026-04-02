import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

MONDAY_TOKEN = os.getenv("MONDAY_API_TOKEN")
ITEM_ID = 11206327226

def get_monday_headers():
    return {
        "Authorization": MONDAY_TOKEN,
        "API-Version": "2023-10",
        "Content-Type": "application/json"
    }

def inspect_updates():
    print(f"--- Inspecting Updates for {ITEM_ID} ---")
    url = "https://api.monday.com/v2"
    query = f'''
    query {{
        items (ids: [{ITEM_ID}]) {{
            name
            updates {{
                id
                body
                created_at
            }}
            column_values {{
                id
                text
                title
            }}
        }}
    }}
    '''
    try:
        resp = requests.post(url, json={"query": query}, headers=get_monday_headers())
        data = resp.json()
        item = data.get('data', {}).get('items', [{}])[0]
        
        print(f"Item Name: {item.get('name')}")
        
        print("\nColumns:")
        for col in item.get('column_values', []):
            print(f"  - {col['title']} ({col['id']}): {col['text']}")

        print("\nUpdates (Comments):")
        updates = item.get('updates', [])
        if updates:
            for u in updates:
                print(f"  - [{u['created_at']}] {u['body'][:100]}...") 
        else:
            print("  (No updates found)")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_updates()
