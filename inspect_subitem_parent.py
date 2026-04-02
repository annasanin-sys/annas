import requests
from sync_script import get_monday_headers

def check_parent(item_id):
    url = "https://api.monday.com/v2"
    query = f'''
    query {{
        items (ids: [{item_id}]) {{
            id
            name
            parent_item {{
                id
                name
            }}
        }}
    }}
    '''
    try:
        resp = requests.post(url, json={"query": query}, headers=get_monday_headers())
        data = resp.json()
        items = data.get('data', {}).get('items', [])
        if items:
            item = items[0]
            parent = item.get('parent_item')
            print(f"Item {item['id']} ({item['name']}):")
            if parent:
                print(f"  -> Parent: {parent['id']} ({parent['name']})")
            else:
                print(f"  -> Parent: None")
            return parent['id'] if parent else None
        else:
            print(f"Item {item_id} not found.")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    SUBITEM_ID = "10848107331"
    NEW_PARENT_ID = "10848496988"
    
    print(f"Checking Subitem {SUBITEM_ID}...")
    actual_parent = check_parent(SUBITEM_ID)
    
    print(f"\nExpected Parent (New): {NEW_PARENT_ID}")
    
    if actual_parent == NEW_PARENT_ID:
        print("MATCH! (Weird)")
    else:
        print("MISMATCH! (Root Cause Identified)")
