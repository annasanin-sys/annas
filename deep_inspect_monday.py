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

def deep_inspect_monday_item():
    query = f'''
    query {{
        items (ids: [{TEST_ITEM_ID}]) {{
            id
            name
            updates {{
                id
                body
                created_at
            }}
            column_values {{
                id
                text
                type
                value
                ... on MirrorValue {{
                    display_value
                }}
            }}
        }}
    }}
    '''
    print(f"Deep inspecting Item {TEST_ITEM_ID}...")
    try:
        resp = requests.post("https://api.monday.com/v2", json={"query": query}, headers=get_monday_headers())
        data = resp.json()
        
        # Dump to file for easier reading
        with open("monday_item_dump.json", "w") as f:
            json.dump(data, f, indent=2)
            
        print("Monday item dump saved to monday_item_dump.json")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    deep_inspect_monday_item()
