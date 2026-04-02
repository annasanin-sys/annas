import json
import os
import requests
from sync_script import update_monday_item, get_monday_headers, MONDAY_BOARD_ID, MONDAY_SUBITEM_BOARD_ID

def debug_update(item_id):
    print(f"Testing update on missing item: {item_id}")
    
    # We'll use the code from sync_script basically, but instrumented
    url = "https://api.monday.com/v2"
    col_vals = json.dumps({"name": "Debug Update"}).replace('"', '\\"')
    
    query = f'''
    mutation {{
        change_multiple_column_values (item_id: {item_id}, board_id: {MONDAY_SUBITEM_BOARD_ID}, column_values: "{col_vals}") {{
            id
        }}
    }}
    '''
    
    try:
        resp = requests.post(url, json={"query": query}, headers=get_monday_headers())
        data = resp.json()
        print("Raw Response:", json.dumps(data, indent=2))
        
        if "errors" in data:
            for err in data["errors"]:
                print(f"Error Message: {err.get('message')}")
                
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    # Use one of the known missing IDs from previous step
    MISSING_ID = "10848107331" 
    debug_update(MISSING_ID)
