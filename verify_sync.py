import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

MONDAY_TOKEN = os.getenv("MONDAY_API_TOKEN")
MONDAY_SUBITEM_BOARD_ID = "18393136039" 
TEST_ITEM_ID = "10847888490"

def get_monday_headers():
    return {
        "Authorization": MONDAY_TOKEN,
        "API-Version": "2023-10",
        "Content-Type": "application/json"
    }

def verify_column_value():
    query = f'''
    query {{
        items (ids: [{TEST_ITEM_ID}]) {{
            name
            column_values (ids: ["long_text_mkyyh8gb"]) {{
                id
                text
                value
            }}
        }}
    }}
    '''
    print(f"Verifying Item {TEST_ITEM_ID}...")
    try:
        resp = requests.post("https://api.monday.com/v2", json={"query": query}, headers=get_monday_headers())
        data = resp.json()
        item = data.get('data', {}).get('items', [])[0]
        
        print(f"Item: {item['name']}")
        cols = item.get('column_values', [])
        for c in cols:
            print(f"Column [{c['id']}] Value: {c['text']}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_column_value()
