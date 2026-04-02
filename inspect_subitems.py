import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

MONDAY_TOKEN = os.getenv("MONDAY_API_TOKEN")
# We need a parent item ID that definitely has subitems now
# I'll rely on the user having 0 main items, but the sync script *should* have created parents.
# I'll fetch main board items, pick one, and fetch its subitems (if any).

def get_monday_headers():
    return {
        "Authorization": MONDAY_TOKEN,
        "API-Version": "2023-10",
        "Content-Type": "application/json"
    }

def inspect_subitems():
    MONDAY_BOARD_ID = os.getenv("MONDAY_BOARD_ID")
    url = "https://api.monday.com/v2"
    
    # 1. Get a parent item
    query_parent = f'''
    query {{
        boards (ids: {MONDAY_BOARD_ID}) {{
            items_page (limit: 5) {{
                items {{
                    id
                    name
                    subitems {{
                        id
                        name
                        board {{
                             id
                             columns {{
                                 id
                                 title
                                 type
                                 settings_str
                             }}
                        }}
                        column_values {{
                            id
                            text
                            ... on StatusValue {{
                                index
                                label
                            }}
                        }}
                    }}
                }}
            }}
        }}
    }}
    '''
    
    try:
        resp = requests.post(url, json={"query": query_parent}, headers=get_monday_headers())
        data = resp.json()
        items = data.get('data', {}).get('boards', [{}])[0].get('items_page', {}).get('items', [])
        
        if not items:
            print("No parent items found.")
            return

        print(f"Found {len(items)} parent items.")
        
        for item in items:
            subs = item.get('subitems', [])
            if subs:
                print(f"Parent: {item['name']} (ID: {item['id']}) has {len(subs)} subitems.")
                first_sub = subs[0]
                print(f"  First Subitem: {first_sub['name']} (ID: {first_sub['id']})")
                print("  Subitem Board Columns:")
                if first_sub.get('board'):
                    for col in first_sub['board']['columns']:
                        print(f"    - {col['title']} (ID: {col['id']}, Type: {col['type']})")
                        if col['type'] == 'status':
                            try:
                                settings = json.loads(col.get('settings_str', '{}'))
                                print("      Labels:", settings.get('labels'))
                            except: pass
                
                print("  Subitem Values:")
                for cv in first_sub.get('column_values', []):
                     print(f"    - ID: {cv['id']}, Text: '{cv['text']}'")
                
                return # Only need one
            
        print("No subitems found on any of the first 5 parents.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_subitems()
