import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

MONDAY_TOKEN = os.getenv("MONDAY_API_TOKEN")
MONDAY_SUBITEM_BOARD_ID = "18393136039" 
TEST_ITEM_ID = "10847888490" # From previous test

def get_monday_headers():
    return {
        "Authorization": MONDAY_TOKEN,
        "API-Version": "2023-10",
        "Content-Type": "application/json"
    }

def create_and_test_checklist():
    url = "https://api.monday.com/v2"
    
    # 1. Create Column
    print("Creating 'Real Checklist' column...")
    query_create = f'''
    mutation {{
        create_column (board_id: {MONDAY_SUBITEM_BOARD_ID}, title: "Real Checklist", column_type: checklist) {{
            id
            title
        }}
    }}
    '''
    checklist_col_id = None
    try:
        resp = requests.post(url, json={"query": query_create}, headers=get_monday_headers())
        data = resp.json()
        if 'errors' in data:
            print("Error creating column:", data)
            # Maybe it already exists? Let's check columns dump if needed.
            # But assume we use whatever ID we get or if it fails we check existing.
        else:
            new_col = data.get('data', {}).get('create_column', {})
            checklist_col_id = new_col.get('id')
            print(f"Created Column: {new_col}")
    except Exception as e:
        print(f"Error: {e}")
        return

    if not checklist_col_id:
        print("Failed to create column. Trying to find existing 'Real Checklist'...")
        # ... fetch columns ...
        # For now, just abort if create failed, assuming simple test.
        return

    # 2. Update Column
    # Format for checklist column?
    # Usually: {"checklists": [{"keys": [{"key": "Item 1", "is_checked": false}]}]} ??
    # Actually Monday API docs say: impossible to update checklist column via API?
    # Wait, in 2023-10 version, `checklist` column update is limited or different.
    # Actually, it might be possible via `create_update` (adding checklist to an update)?
    # BUT, the column itself...
    # Let's try to update it with a simple string or JSON.
    
    # Try 1: text representation?
    print(f"Attempting to write to {checklist_col_id}...")
    
    # This structure is a guess based on some docs, might fail.
    # Monday Checklist column value structure:
    # { "s_title": "My List", "z_list": [ { "name": "Item 1", "checked": false } ] } ?
    # Note: Automation and API support for Checklist column is notoriously poor.
    # Better approach might be: Use the "Checklist" widget in Updates?
    
    # But let's try writing standard JSON structure.
    # According to one community post:
    # Invalid column type for update?
    
    val = json.dumps({"name": "Test Item"}).replace('"', '\\"') # Just filler
    
    query_update = f'''
    mutation {{
        change_multiple_column_values (item_id: {TEST_ITEM_ID}, board_id: {MONDAY_SUBITEM_BOARD_ID}, column_values: "{{\\"{checklist_col_id}\\": \\"Test\\"}}") {{
            id
        }}
    }}
    '''
    # We will try sending a string first.
    
    try:
        resp = requests.post(url, json={"query": query_update}, headers=get_monday_headers())
        print("Update Response:", json.dumps(resp.json(), indent=2))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    create_and_test_checklist()
